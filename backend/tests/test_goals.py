from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app import goals
from app.auth import get_token_verifier
from app.main import app

PATH = "/api/v1/goals"


@pytest.fixture
def goal_client(monkeypatch, token_verifier, access_token):
    rows = []
    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = (True,)
    cursor = connection.cursor.return_value.__enter__.return_value

    def execute(query, parameters):
        if "INSERT INTO" in query:
            goal_id, owner, title = parameters
            goal = goals.Goal(id=goal_id, title=title, created_at=datetime.now(UTC))
            rows.append((owner, goal))
            cursor.fetchone.return_value = goal
        elif "WHERE owner_id = %s" in query:
            (owner,) = parameters
            cursor.fetchall.return_value = [goal for user, goal in rows if user == owner]
        else:
            pytest.fail("Unexpected goals query")

    cursor.execute.side_effect = execute

    @contextmanager
    def fake_connection():
        yield connection

    monkeypatch.setattr(goals, "database_connection", fake_connection)
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    with TestClient(app) as client:
        yield client, connection, lambda user: {"Authorization": f"Bearer {access_token(subject=user)}"}


def test_goals_require_authentication(goal_client):
    client, connection, _ = goal_client
    assert client.get(PATH).status_code == 401
    assert client.post(PATH, json={"title": "Try goals"}).status_code == 401
    connection.execute.assert_not_called()


def test_goals_are_scoped_to_the_verified_subject(goal_client, user_a, user_b):
    client, connection, auth = goal_client
    a, b = auth(user_a.subject), auth(user_b.subject)
    title = "  Read O'Reilly's guide  "

    created = client.post(PATH, json={"title": title}, headers=a)
    assert created.status_code == 201
    goal = created.json()
    assert set(goal) == {"id", "title", "created_at"}
    assert goal["title"] == title.strip()
    assert connection.execute.call_args.args[1] == (user_a.subject,)

    assert client.get(PATH, headers=b).json() == []
    assert connection.execute.call_args.args[1] == (user_b.subject,)
    assert client.patch(f"{PATH}/{goal['id']}", json={"title": "Changed"}, headers=b).status_code == 404
    assert client.delete(f"{PATH}/{goal['id']}", headers=b).status_code == 404
    assert client.get(PATH, headers=a).json() == [goal]


@pytest.mark.parametrize("payload", [
    {"title": "Spoofed", "owner_id": "test-user-a"},
    {"title": "  "},
    {"title": "x" * 201},
])
def test_invalid_creation_payload_does_not_touch_database(goal_client, user_b, payload):
    client, connection, auth = goal_client
    response = client.post(PATH, headers=auth(user_b.subject), json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    connection.execute.assert_not_called()


def test_goals_fail_closed_if_database_role_bypasses_rls(goal_client, user_a):
    client, connection, auth = goal_client
    connection.execute.return_value.fetchone.return_value = (False,)
    response = client.get(PATH, headers=auth(user_a.subject))
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "GOALS_UNAVAILABLE"
    connection.cursor.assert_not_called()
