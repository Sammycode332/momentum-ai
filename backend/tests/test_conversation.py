from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import conversation, planning_provider
from app.api_errors import ApiError
from app.auth import get_token_verifier
from app.main import app

PATH = "/api/v1/ai/chat"


@pytest.fixture(autouse=True)
def isolated_personalization(monkeypatch):
    monkeypatch.setattr(conversation, 'personalization_enabled', lambda owner: True)
    monkeypatch.setattr(conversation, 'relevant_memories', lambda owner, query: [])

MESSAGES = [
    {"role": "user", "content": "Explain dependency injection."},
    {"role": "assistant", "content": "It supplies dependencies from outside."},
    {"role": "user", "content": "How does that apply in FastAPI?"},
]


def test_chat_history_and_workspace_use_verified_identity(monkeypatch, token_verifier, access_token):
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    record_id = uuid4()
    contexts = Mock(side_effect=lambda owner: {
        "tasks": [{"id": record_id, "title": owner + " task", "project_id": None}], "projects": [],
    })
    provider = Mock()
    provider.generate.return_value = '{"reply":"FastAPI supplies dependencies through Depends."}'
    monkeypatch.setattr(conversation, "load_planning_context", contexts)
    monkeypatch.setattr(conversation, "get_planning_provider", lambda: provider)
    with TestClient(app) as client:
        assert client.post(PATH, json={"messages": MESSAGES}).status_code == 401
        assert client.post(PATH, json={"messages": MESSAGES}, headers={"Authorization": "Bearer invalid"}).status_code == 401
        contexts.assert_not_called()
        for owner in ("user-a", "user-b"):
            headers = {"Authorization": f"Bearer {access_token(subject=owner)}"}
            assert client.post(PATH, json={"messages": MESSAGES[:2]}, headers=headers).status_code == 422
            assert client.post(PATH, json={"messages": MESSAGES, "owner_id": "other"}, headers=headers).status_code == 422
            response = client.post(PATH, json={"messages": MESSAGES}, headers=headers)
            assert response.status_code == 200
            assert response.headers["cache-control"] == "no-store"
            assert "Depends" in response.json()["reply"]
            payload = provider.generate.call_args.args[0]
            assert payload["messages"] == MESSAGES
            assert payload["workspace"]["tasks"] == [{"title": owner + " task", "ref": "T1"}]
        assert [call.args for call in contexts.call_args_list] == [("user-a",), ("user-b",)]
        provider.generate.side_effect = ApiError(429, "AI_RATE_LIMIT", "Try again later.")
        assert client.post(PATH, json={"messages": MESSAGES}, headers=headers).status_code == 429
        provider.generate.side_effect = None
        provider.generate.return_value = '{"reply":" "}'
        assert client.post(PATH, json={"messages": MESSAGES}, headers=headers).json()["error"]["code"] == "AI_INVALID_REPLY"


def test_gemini_reads_backend_dotenv_and_prefers_nonblank_process_values(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=fixture-local\nGEMINI_MODEL=fixture-model\n", encoding="utf-8-sig")
    monkeypatch.setattr(planning_provider, "ENV_FILE", env_file)
    monkeypatch.setattr(planning_provider, "GeminiProvider", lambda key, model: SimpleNamespace(key=key, model=model))
    monkeypatch.setenv("GEMINI_API_KEY", "   ")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert planning_provider.get_planning_provider() == SimpleNamespace(key="fixture-local", model="fixture-model")
    monkeypatch.setenv("GEMINI_API_KEY", "fixture-process")
    assert planning_provider.get_planning_provider().key == "fixture-process"
    monkeypatch.delenv("GEMINI_API_KEY")
    env_file.write_text("GEMINI_API_KEY=\n", encoding="utf-8")
    with pytest.raises(ApiError) as failure:
        planning_provider.get_planning_provider()
    assert failure.value.code == "AI_NOT_CONFIGURED"
    env_file.write_text("GEMINI_API_KEY=fixture-local\n", encoding="utf-8")
    with pytest.raises(ApiError) as failure:
        planning_provider.get_planning_provider()
    assert failure.value.code == "AI_MODEL_NOT_CONFIGURED"


@pytest.mark.parametrize("follow_up", [
    "Use my learning goals to suggest an example.",
    "Unrelated question: how do tides work? Two sentences, please.",
])
def test_mentor_prompt_preserves_followups_and_limits_personalization(
    monkeypatch, token_verifier, access_token, follow_up,
):
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    monkeypatch.setattr(conversation, "load_planning_context", lambda _: {
        "tasks": [], "projects": [], "primary_focus": "Music",
    })
    provider = Mock()
    provider.generate.return_value = '{"reply":"## A simple example"}'
    monkeypatch.setattr(conversation, "get_planning_provider", lambda: provider)
    history = [*MESSAGES[:2], {"role": "user", "content": follow_up}]
    with TestClient(app) as client:
        response = client.post(PATH, json={"messages": history},
                               headers={"Authorization": f"Bearer {access_token()}"})
    assert response.json() == {"reply": "## A simple example"}
    call = provider.generate.call_args
    assert call.args[0]["messages"] == history
    assert call.args[0]["workspace"]["primary_focus"] == "Music"
    instructions = call.kwargs["instructions"]
    assert "leave unrelated workspace context out" in instructions
    assert "build on the learner's previous answer" in instructions
    assert "Honor explicit requests for brevity, depth, and format" in instructions


def test_unexpected_chat_failure_has_redacted_correlated_diagnostics(
    monkeypatch, token_verifier, access_token, caplog,
):
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    monkeypatch.setattr(conversation, "get_planning_provider", Mock())
    monkeypatch.setattr(conversation, "load_planning_context",
                        Mock(side_effect=RuntimeError("synthetic private context")))
    with TestClient(app) as client:
        response = client.post(
            PATH, json={"messages": MESSAGES},
            headers={"Authorization": f"Bearer {access_token()}"},
        )
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"] in caplog.text
    assert "RuntimeError" in caplog.text
    assert "/api/v1/ai/chat" in caplog.text
    assert "synthetic private context" not in caplog.text + response.text


def test_chat_api_replaces_unconfirmed_provider_success(monkeypatch, token_verifier, access_token):
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    monkeypatch.setattr(conversation, "load_planning_context", lambda _: {})
    provider = Mock()
    provider.generate.return_value = '{"reply":"I have added it to your tasks."}'
    monkeypatch.setattr(conversation, "get_planning_provider", lambda: provider)
    with TestClient(app) as client:
        response = client.post(PATH, json={"messages": MESSAGES},
                               headers={"Authorization": f"Bearer {access_token()}"})
    assert response.status_code == 200
    assert response.json() == {"reply": "I can only confirm workspace changes after an approved action succeeds."}
