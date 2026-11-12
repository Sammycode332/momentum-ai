from fastapi.testclient import TestClient

from app.main import app


def test_openapi_has_no_application_paths() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["paths"] == {}


def test_controlled_principals_are_distinct(
    user_a,
    user_b,
    privileged_actor,
) -> None:
    assert user_a.subject != user_b.subject
    assert privileged_actor.subject not in {user_a.subject, user_b.subject}
    assert privileged_actor.access == "privileged"
