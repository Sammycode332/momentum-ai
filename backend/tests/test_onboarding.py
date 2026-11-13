from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app import onboarding
from app.auth import get_token_verifier
from app.main import app

PATH = "/api/v1/onboarding"
PREFERENCES = {
    "primary_focus": "Study",
    "current_goals": "Finish the first chapter",
    "planning_time": "08:30",
}


@pytest.fixture
def onboarding_client(monkeypatch, token_verifier, access_token):
    rows = {}
    connection = MagicMock()
    context = connection.execute.return_value
    context.fetchone.return_value = (True,)
    cursor = connection.cursor.return_value.__enter__.return_value

    def execute(query, parameters=None):
        if "set_config" in query:
            (connection.owner,) = parameters
        elif "DO NOTHING" in query:
            (owner,) = parameters
            assert owner == connection.owner
            rows.setdefault(owner, onboarding.Onboarding(
                status="skipped", primary_focus=None, current_goals=None, planning_time=None,
            ))
        elif "DO UPDATE" in query:
            owner, focus, goals, time = parameters
            assert owner == connection.owner
            rows[owner] = onboarding.Onboarding(
                status="completed", primary_focus=focus, current_goals=goals, planning_time=time,
            )
        else:
            assert "row_security_active" in query
        return context

    def read(query, parameters):
        assert "WHERE owner_id = %s" in query
        (owner,) = parameters
        assert owner == connection.owner
        cursor.fetchone.return_value = rows.get(owner)

    connection.execute.side_effect = execute
    cursor.execute.side_effect = read

    @contextmanager
    def fake_connection():
        yield connection

    monkeypatch.setattr(onboarding, "database_connection", fake_connection)
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    with TestClient(app) as client:
        yield client, connection, lambda subject: {
            "Authorization": f"Bearer {access_token(subject=subject)}"
        }


def test_onboarding_requires_authentication(onboarding_client):
    client, connection, _ = onboarding_client
    assert client.get(PATH).status_code == 401
    assert client.put(PATH, json=PREFERENCES).status_code == 401
    assert client.post(f"{PATH}/skip").status_code == 401
    connection.execute.assert_not_called()


def test_complete_edit_and_skip_are_private(onboarding_client, user_a, user_b):
    client, _, auth = onboarding_client
    a, b = auth(user_a.subject), auth(user_b.subject)
    assert client.get(PATH, headers=a).json() is None
    saved = client.put(PATH, headers=a, json=PREFERENCES)
    assert saved.status_code == 200
    assert saved.headers["cache-control"] == "no-store"
    assert saved.json() == {"status": "completed", **PREFERENCES}
    assert client.get(PATH, headers=b).json() is None
    skipped = client.post(f"{PATH}/skip", headers=b).json()
    assert skipped == {
        "status": "skipped", "primary_focus": None, "current_goals": None, "planning_time": None,
    }
    assert client.get(PATH, headers=b).json() == skipped
    assert client.put(PATH, headers=b, json={**PREFERENCES, "primary_focus": "Career"}).status_code == 200
    assert client.get(PATH, headers=a).json() == saved.json()
    updated = {**PREFERENCES, "planning_time": "17:45"}
    assert client.put(PATH, headers=a, json=updated).json() == {"status": "completed", **updated}
    assert client.post(f"{PATH}/skip", headers=a).json() == client.get(PATH, headers=a).json()
    assert client.get(PATH, headers=b).json()["primary_focus"] == "Career"


@pytest.mark.parametrize("override", [
    {"owner_id": "test-user-a"},
    {"planning_time": "24:00"},
    {"primary_focus": "  "},
    {"current_goals": "x" * 1001},
])
def test_invalid_preferences_are_rejected(onboarding_client, override):
    client, connection, auth = onboarding_client
    result = client.put(PATH, headers=auth("test-user-b"), json={**PREFERENCES, **override})
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "INVALID_REQUEST"
    connection.execute.assert_not_called()


def test_onboarding_requires_active_rls(onboarding_client):
    client, connection, auth = onboarding_client
    connection.execute.return_value.fetchone.return_value = (False,)
    assert client.get(PATH, headers=auth("test-user-a")).status_code == 503
    connection.cursor.assert_not_called()
