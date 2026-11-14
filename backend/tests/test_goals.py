from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

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
        elif query.lstrip().startswith("UPDATE"):
            assert "WHERE id = %s AND owner_id = %s" in query
            title, completed, goal_id, owner = parameters
            cursor.fetchone.return_value = None
            for index, (user, goal) in enumerate(rows):
                if user == owner and goal.id == goal_id:
                    saved = goal.model_copy(update={
                        "title": goal.title if title is None else title,
                        "completed": goal.completed if completed is None else completed,
                    })
                    rows[index] = (user, saved)
                    cursor.fetchone.return_value = saved
        elif query.lstrip().startswith("DELETE"):
            assert "WHERE id = %s AND owner_id = %s" in query
            goal_id, owner = parameters
            before = len(rows)
            rows[:] = [(user, goal) for user, goal in rows if not (user == owner and goal.id == goal_id)]
            cursor.rowcount = before - len(rows)
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
    assert client.patch(f"{PATH}/{uuid4()}", json={"completed": True}).status_code == 401
    assert client.delete(f"{PATH}/{uuid4()}").status_code == 401
    connection.execute.assert_not_called()


def test_goals_are_scoped_to_the_verified_subject(goal_client, user_a, user_b):
    client, connection, auth = goal_client
    a, b = auth(user_a.subject), auth(user_b.subject)
    title = "  Read O'Reilly's guide  "

    created = client.post(PATH, json={"title": title}, headers=a)
    assert created.status_code == 201
    goal = created.json()
    assert set(goal) == {"id", "title", "created_at", "completed"}
    assert goal["completed"] is False
    assert goal["title"] == title.strip()
    assert connection.execute.call_args.args[1] == (user_a.subject,)

    assert client.get(PATH, headers=b).json() == []
    assert connection.execute.call_args.args[1] == (user_b.subject,)
    assert client.patch(f"{PATH}/{goal['id']}", json={"title": "Changed"}, headers=b).status_code == 404
    assert client.delete(f"{PATH}/{goal['id']}", headers=b).status_code == 404
    assert client.get(PATH, headers=a).json() == [goal]


def test_owner_can_edit_complete_reopen_and_delete(goal_client):
    client, connection, auth = goal_client
    headers = auth("test-owner")
    goal = client.post(PATH, json={"title": "Synthetic"}, headers=headers).json()
    path = f"{PATH}/{goal['id']}"
    renamed = client.patch(path, json={"title": "  New title  "}, headers=headers)
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "New title"
    assert not renamed.json()["completed"]
    assert renamed.headers["cache-control"] == "no-store"
    completed = client.patch(path, json={"completed": True}, headers=headers)
    assert completed.json()["completed"] is True
    assert completed.json()["title"] == "New title"
    cursor = connection.cursor.return_value.__enter__.return_value
    assert cursor.execute.call_args.args[1] == (None, True, UUID(goal["id"]), "test-owner")
    reopened = client.patch(path, json={"completed": False}, headers=headers)
    assert reopened.json()["completed"] is False
    deleted = client.delete(path, headers=headers)
    assert deleted.status_code == 204 and not deleted.content
    assert client.get(PATH, headers=headers).json() == []
    assert client.delete(path, headers=headers).status_code == 404


@pytest.mark.parametrize("payload", [{}, {"title": None}, {"completed": None},
    {"completed": "true"}, {"completed": 1}, {"title": " "}, {"title": "x" * 201},
    {"title": "bad\0text"}, {"title": "Good", "owner_id": "other"}])
def test_invalid_update_does_not_touch_database(goal_client, payload):
    client, connection, auth = goal_client
    result = client.patch(f"{PATH}/{uuid4()}", json=payload, headers=auth("test-owner"))
    assert result.status_code == 422
    connection.execute.assert_not_called()


@pytest.mark.parametrize("method,payload", [("patch", {"completed": True}), ("delete", None)])
def test_mutations_fail_closed_when_rls_inactive(goal_client, method, payload):
    client, connection, auth = goal_client
    connection.execute.return_value.fetchone.return_value = (False,)
    result = client.request(method, f"{PATH}/{uuid4()}", json=payload, headers=auth("test-owner"))
    assert result.status_code == 503
    connection.cursor.assert_not_called()


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
