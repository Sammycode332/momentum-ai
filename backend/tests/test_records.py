from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app import records
from app.auth import get_token_verifier
from app.main import app


@pytest.mark.parametrize("domain,payload", [
    ("projects", {"name": "bad\0title"}),
    ("tasks", {"title": "Synthetic", "description": "bad\0description"}),
    ("academics", {"activity": "Synthetic", "description": "x" * 4001}),
    ("projects", {"name": "Synthetic", "description": "x" * 4001}),
    ("tasks", {"title": "Synthetic", "description": "x" * 4001}),
    ("learning", {"subject": "Synthetic", "objective": "bad\0objective"}),
    ("opportunities", {"name": "Synthetic", "type": "bad\0type"}),
    ("opportunities", {"name": "Synthetic", "type": "job", "url": "https://example.test/\0"}),
    ("tasks", {"title": "Synthetic", "owner_id": "other-user"}),
])
@pytest.mark.parametrize("method", ["post", "put"])
def test_invalid_records_are_rejected_before_database_access(
    monkeypatch, token_verifier, access_token, domain, payload, method,
):
    connection = Mock(side_effect=AssertionError("Invalid input reached storage"))
    monkeypatch.setattr(records, "records_connection", connection)
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    suffix = "/00000000-0000-4000-8000-000000000001" if method == "put" else ""
    with TestClient(app) as client:
        response = getattr(client, method)(
            f"/api/v1/{domain}{suffix}", json=payload,
            headers={"Authorization": f"Bearer {access_token()}"},
        )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    connection.assert_not_called()


def test_description_boundary_and_optional_empty_values():
    assert len(records.ProjectInput(name="Synthetic", description="x" * 4000).description) == 4000
    assert records.TaskInput(title="Synthetic", description="").description == ""
    assert records.AcademicInput(activity="Synthetic").description is None
