from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.auth import InvalidAccessTokenError, get_token_verifier
from app.main import app


def test_openapi_includes_the_private_api_routes() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert set(response.json()["paths"]) >= {
        "/api/v1/auth/me", "/api/v1/goals", "/api/v1/onboarding", "/api/v1/onboarding/skip",
        "/api/v1/goals/{goal_id}",
        "/api/v1/{domain}", "/api/v1/{domain}/{record_id}", "/api/v1/ai/plan", "/api/v1/ai/chat",
        "/api/v1/ai/conversations", "/api/v1/ai/conversations/{chat_id}",
        "/api/v1/ai/conversations/{chat_id}/messages", "/api/v1/ai/conversations/{chat_id}/turns",
    }


def test_controlled_principals_are_distinct(
    user_a,
    user_b,
    privileged_actor,
) -> None:
    assert user_a.subject != user_b.subject
    assert privileged_actor.subject not in {user_a.subject, user_b.subject}
    assert privileged_actor.access == "privileged"


def test_verifier_derives_the_subject_from_a_valid_token(
    token_verifier,
    access_token,
) -> None:
    principal = token_verifier.verify(access_token(subject="test-user-a"))

    assert principal.subject == "test-user-a"


def test_verifier_rejects_an_expired_token(token_verifier, access_token) -> None:
    expired_token = access_token(expires_in=timedelta(seconds=-1))

    with pytest.raises(InvalidAccessTokenError):
        token_verifier.verify(expired_token)


def test_verifier_rejects_a_token_from_another_issuer(
    token_verifier,
    access_token,
) -> None:
    other_issuer_token = access_token(issuer="https://other-auth.example.test")

    with pytest.raises(InvalidAccessTokenError):
        token_verifier.verify(other_issuer_token)


def test_protected_endpoint_rejects_missing_and_malformed_tokens(token_verifier, caplog) -> None:
    app.dependency_overrides[get_token_verifier] = lambda: token_verifier
    try:
        with TestClient(app) as client:
            missing = client.get("/api/v1/auth/me")
            malformed = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer not-a-jwt"},
            )
    finally:
        app.dependency_overrides.clear()

    assert missing.status_code == 401
    assert missing.json() == {
        "error": {
            "code": "UNAUTHORIZED",
            "message": "Authentication is required.",
        }
    }
    assert malformed.status_code == 401
    assert f"id={malformed.headers['x-request-id']} reason=DecodeError" in caplog.text
    assert "not-a-jwt" not in caplog.text
    assert malformed.json() == {
        "error": {
            "code": "INVALID_ACCESS_TOKEN",
            "message": "The access token is invalid or expired.",
        }
    }


def test_protected_endpoint_returns_only_the_verified_subject(
    token_verifier,
    access_token,
) -> None:
    app.dependency_overrides[get_token_verifier] = lambda: token_verifier
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token(subject='test-user-b')}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"subject": "test-user-b"}


def test_protected_endpoint_distinguishes_expired_token(monkeypatch, token_verifier, access_token):
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    token = access_token(expires_in=timedelta(seconds=-1))
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "ACCESS_TOKEN_EXPIRED"


@pytest.mark.parametrize("claim", ["iat", "nbf"])
def test_future_tokens_are_diagnosed_without_accepting_them(
    monkeypatch, token_verifier, token_signing_key, neon_auth_settings, claim, caplog,
):
    from datetime import UTC, datetime
    import jwt

    now = datetime.now(UTC)
    token = jwt.encode({
        "sub": "synthetic-user", "iss": neon_auth_settings.issuer,
        "exp": now + timedelta(minutes=5), claim: now + timedelta(minutes=1),
    }, token_signing_key, algorithm="EdDSA", headers={"kid": "test-key"})
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "ACCESS_TOKEN_NOT_YET_VALID"
    assert "ImmatureSignatureError" in caplog.text
    assert token not in caplog.text
    assert "synthetic-user" not in caplog.text
