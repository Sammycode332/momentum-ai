import json
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from google import genai
from google.genai import errors

from app import planning, planning_context
from app.auth import get_token_verifier
from app.main import app
from app.planning_provider import GeminiProvider

PATH = "/api/v1/ai/plan"
REQUEST = {"objective": "Prepare my draft", "available_minutes": 30}


def draft(**activity_changes):
    return json.dumps({
        "title": "Draft session", "summary": "Prepare the first draft.",
        "activities": [{
            "title": "Draft the outline", "duration_minutes": 20, "reason": "It is due soon.",
            "task_ref": "T1", "project_ref": "P1", **activity_changes,
        }],
        "deadline_considerations": ["Set aside time for review."],
    })


@pytest.fixture
def harness(monkeypatch, token_verifier, access_token):
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    task_id, project_id = uuid4(), uuid4()
    context = Mock(return_value={
        "tasks": [{"id": task_id, "title": "Outline", "project_id": project_id}],
        "projects": [{"id": project_id, "name": "Essay"}],
    })
    provider = Mock()
    provider.generate.return_value = draft()
    monkeypatch.setattr(planning, "load_planning_context", context)
    monkeypatch.setattr(planning, "get_planning_provider", lambda: provider)
    headers = {"Authorization": f"Bearer {access_token(subject='fixture-owner')}"}
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, headers=headers, provider=provider, context=context,
                              task_id=task_id, project_id=project_id)


def test_planning_uses_verified_subject_and_resolves_only_real_records(harness):
    response = harness.client.post(PATH, json=REQUEST, headers=harness.headers)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["total_minutes"] == 20
    assert response.json()["activities"][0]["task"] == {"id": str(harness.task_id), "title": "Outline"}
    assert response.json()["activities"][0]["project"]["id"] == str(harness.project_id)
    harness.context.assert_called_once_with("fixture-owner")
    payload, schema = harness.provider.generate.call_args.args
    assert payload["workspace"]["tasks"][0]["project_ref"] == "P1"
    assert str(harness.task_id) not in json.dumps(payload)
    assert "fixture-owner" not in json.dumps(payload)
    assert schema["properties"]["activities"]["maxItems"] == 8


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer invalid"}])
def test_planning_requires_authentication(harness, headers):
    assert harness.client.post(PATH, json=REQUEST, headers=headers).status_code == 401
    harness.context.assert_not_called()
    harness.provider.generate.assert_not_called()


@pytest.mark.parametrize("changes", [
    {"owner_id": "another-user"}, {"objective": "   "}, {"available_minutes": 481},
    {"available_minutes": "30"}, {"focus_area": "x" * 121},
])
def test_planning_validates_input(harness, changes):
    response = harness.client.post(PATH, json={**REQUEST, **changes}, headers=harness.headers)
    assert response.status_code == 422
    harness.context.assert_not_called()


@pytest.mark.parametrize("output", [
    "private invalid JSON", draft(duration_minutes=31), draft(task_ref="T99"),
    draft(project_ref="T1"), draft(duration_minutes="20"),
])
def test_invalid_provider_output_is_rejected(harness, output):
    harness.provider.generate.return_value = output
    response = harness.client.post(PATH, json=REQUEST, headers=harness.headers)
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "AI_INVALID_PLAN"
    assert output not in response.text


@pytest.mark.parametrize(("failure", "status", "code"), [
    (httpx.ReadTimeout("private timeout"), 504, "AI_TIMEOUT"),
    (errors.ClientError(429, {"error": {"message": "private quota"}}), 429, "AI_RATE_LIMIT"),
    (errors.ClientError(404, {"error": {"message": "private model"}}), 503, "AI_MODEL_UNAVAILABLE"),
    (errors.ServerError(503, {"error": {"message": "private outage"}}), 502, "AI_PROVIDER_ERROR"),
])
def test_provider_failures_are_safe(harness, monkeypatch, failure, status, code):
    sdk = Mock()
    sdk.models.generate_content.side_effect = failure
    monkeypatch.setattr(genai, "Client", lambda **kwargs: nullcontext(sdk))
    monkeypatch.setattr(planning, "get_planning_provider", lambda: GeminiProvider("synthetic", "model"))
    response = harness.client.post(PATH, json=REQUEST, headers=harness.headers)
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert "private" not in response.text
    sdk.models.generate_content.assert_called_once()


def test_gemini_requests_structured_output_with_a_single_bounded_attempt(monkeypatch):
    sdk = Mock()
    sdk.models.generate_content.return_value.text = draft()
    client = Mock(return_value=nullcontext(sdk))
    monkeypatch.setattr(genai, "Client", client)
    schema = planning.DraftPlan.model_json_schema()
    assert GeminiProvider("synthetic", "model").generate({"request": REQUEST}, schema) == draft()
    options = client.call_args.kwargs["http_options"]
    assert options.timeout == 45_000
    assert options.retry_options.attempts == 1
    call = sdk.models.generate_content.call_args.kwargs
    assert call["model"] == "model"
    assert call["config"].response_json_schema == schema
    assert call["config"].tools is None


def test_context_queries_scope_every_domain_and_bound_results(monkeypatch, user_a, user_b):
    records, goals, onboarding = Mock(), Mock(), Mock()
    cursor = Mock()
    records.cursor.return_value = nullcontext(cursor)
    cursor.execute.return_value.fetchall.return_value = []
    goals.execute.return_value.fetchall.return_value = [("A goal",)]
    reads = Mock(return_value=SimpleNamespace(status="completed", primary_focus="Study"))
    monkeypatch.setattr(planning_context, "read_onboarding", reads)
    for name, connection in (("records", records), ("goals", goals), ("onboarding", onboarding)):
        monkeypatch.setattr(planning_context, f"{name}_connection", Mock(return_value=nullcontext(connection)))
    for principal in (user_a, user_b):
        result = planning_context.load_planning_context(principal.subject)
        assert result["primary_focus"] == "Study"
    for index, principal in enumerate((user_a, user_b)):
        calls = cursor.execute.call_args_list[index * 5:(index + 1) * 5] + [goals.execute.call_args_list[index]]
        for call in calls:
            query, params = call.args
            assert "owner_id = %s" in query and "LIMIT" in query
            assert params == (principal.subject,)
        reads.assert_any_call(onboarding, principal.subject)
        for name in ("records", "goals", "onboarding"):
            getattr(planning_context, f"{name}_connection").assert_any_call(principal.subject)
