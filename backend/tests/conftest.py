from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Literal

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.auth import NeonAccessTokenVerifier, NeonAuthSettings


@dataclass(frozen=True)
class TestPrincipal:
    subject: str
    access: Literal["user", "privileged"]


@pytest.fixture
def user_a() -> TestPrincipal:
    return TestPrincipal(subject="test-user-a", access="user")


@pytest.fixture
def user_b() -> TestPrincipal:
    return TestPrincipal(subject="test-user-b", access="user")


@pytest.fixture
def privileged_actor() -> TestPrincipal:
    return TestPrincipal(subject="test-privileged-actor", access="privileged")


class StaticJwkClient:
    def __init__(self, key: object) -> None:
        self._key = key

    def get_signing_key_from_jwt(self, _: str) -> SimpleNamespace:
        return SimpleNamespace(key=self._key)


@pytest.fixture
def neon_auth_settings() -> NeonAuthSettings:
    return NeonAuthSettings(
        jwks_url="https://jwks.example.test/keys",
        issuer="https://auth.example.test",
    )


@pytest.fixture
def token_signing_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


@pytest.fixture
def token_verifier(
    neon_auth_settings: NeonAuthSettings,
    token_signing_key: Ed25519PrivateKey,
) -> NeonAccessTokenVerifier:
    return NeonAccessTokenVerifier(
        neon_auth_settings,
        jwk_client=StaticJwkClient(token_signing_key.public_key()),
    )


@pytest.fixture
def access_token(
    token_signing_key: Ed25519PrivateKey,
    neon_auth_settings: NeonAuthSettings,
):
    def create(
        *,
        subject: str = "test-user-a",
        issuer: str | None = None,
        expires_in: timedelta = timedelta(minutes=5),
    ) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "sub": subject,
                "iss": issuer or neon_auth_settings.issuer,
                "iat": now,
                "exp": now + expires_in,
            },
            token_signing_key,
            algorithm="EdDSA",
            headers={"kid": "test-key"},
        )

    return create
