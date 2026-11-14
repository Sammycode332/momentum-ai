import os
from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import actions, chat_actions, conversation_history, goal_plans, goals, private_store, records
from app.api_errors import ApiError
from app.auth import get_token_verifier
from app.database import DatabaseError
from app.main import app
from app.task_edits import TaskEdit, apply_task_edit

REQUEST = "Create a high-priority task called 'learn system design' for tomorrow at 6 PM."
DETAILS = '{"title":"learn system design","priority":"high","due_date":"2026-11-15"}'
CHAT = "/api/v1/ai/conversations"


@pytest.mark.parametrize(("instruction", "search", "field", "value"), [
    ("Mark my system design task as completed.", "system design", "status", "completed"),
    ("Change my NeetCode task to high priority.", "NeetCode", "priority", "high"),
    ("Move my database project task to Friday.", "database project", "due_date", "2026-11-20"),
    ("Rename my system design task to Study distributed systems.", "system design", "title", "Study distributed systems"),
])
def test_task_edit_resolves_one_owned_record(monkeypatch, instruction, search, field, value):
    import json
    provider = Mock()
    provider.generate.return_value = json.dumps({"search": search, "field": field, "value": value})
    monkeypatch.setattr(chat_actions, "get_planning_provider", lambda: provider)
    cursor = Mock()
    task = dict(id=uuid4(), title=f"Practice {search}", status="not_started", priority="medium",
                due_date=None, updated_at=datetime.now(UTC), project=None, exact=False)
    cursor.execute.return_value.fetchall.return_value = [task]
    _, proposal = chat_actions.extract_task_edit(cursor, "owner", instruction, "Africa/Lagos")
    assert chat_actions.TASK_EDIT_REQUEST.search(instruction)
    assert proposal.target_id == task["id"]
    assert proposal.edit.field == field and proposal.edit.value == value
    assert cursor.execute.call_args.args[1] == (search, "owner", search)
    cursor.execute.return_value.fetchall.return_value = [task, {**task, "id": uuid4()}]
    reply, proposal = chat_actions.extract_task_edit(cursor, "owner", instruction, "Africa/Lagos")
    assert proposal is None and "Several" in reply


def test_task_edit_requires_a_target_and_preserves_requested_time(monkeypatch):
    provider = Mock()
    monkeypatch.setattr(chat_actions, "get_planning_provider", lambda: provider)
    cursor = Mock()
    provider.generate.return_value = '{"search":null,"field":"title","value":"Study distributed systems"}'
    assert chat_actions.extract_task_edit(cursor, "owner", "Rename my task to Study distributed systems.", "UTC")[1] is None
    provider.generate.return_value = '{"search":"study","field":"due_date","value":"2026-11-20"}'
    assert "exact time" in chat_actions.extract_task_edit(cursor, "owner", "Move my study task to Friday at 6 PM.", "UTC")[0]
    cursor.execute.assert_not_called()
    with pytest.raises(ValidationError):
        TaskEdit(field="priority", value="critical")


def test_task_edit_refuses_a_stale_snapshot():
    cursor = Mock()
    task_id = uuid4()
    edit = TaskEdit(field="title", value="New title", previous="Old title", version=datetime(2026, 11, 14, tzinfo=UTC))
    cursor.execute.return_value.fetchone.return_value = {"title": "Old title", "updated_at": datetime(2026, 11, 15, tzinfo=UTC)}
    with pytest.raises(ApiError) as error:
        apply_task_edit(cursor, "owner", task_id, "Old title", edit)
    assert error.value.code == "TARGET_CHANGED"
    assert cursor.execute.call_count == 1


@pytest.mark.parametrize("claim", [
    "I have added 'Learn system design' to your tasks for tomorrow at 6 PM.",
    "**Done!** Your task is ready.",
    "I’ve updated your task.",
    "Your project was deleted.",
    "Your reminder has been scheduled for tomorrow.",
    "Your task is now on your list.",
])
def test_unconfirmed_workspace_changes_are_suppressed(claim):
    assert chat_actions.safe_chat_reply(claim) == chat_actions.UNCONFIRMED
    assert chat_actions.safe_chat_reply("You can create a task in Tasks.") == "You can create a task in Tasks."


@pytest.mark.parametrize("raw", [
    '{"title":" ","priority":"high","due_date":null}',
    '{"title":"Study","priority":"critical","due_date":null}',
    '{"title":"Study","priority":"high","due_date":"tomorrow"}',
    '{"title":"Study","priority":"high","due_date":null,"owner_id":"other"}',
    '{"title":null,"priority":"medium","due_date":null}',
    '{"reply":"I created the task."}',
])
def test_invalid_or_unclear_details_cannot_produce_proposals(monkeypatch, raw):
    provider = Mock()
    provider.generate.return_value = raw
    monkeypatch.setattr(chat_actions, "get_planning_provider", lambda: provider)
    assert chat_actions.extract_task(REQUEST, "UTC") is None


def test_task_extraction_uses_local_date(monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz):
            return cls(2026, 11, 13, 23, 45, tzinfo=UTC)

    monkeypatch.setattr(chat_actions, "datetime", Clock)
    provider = Mock()
    provider.generate.return_value = DETAILS
    monkeypatch.setattr(chat_actions, "get_planning_provider", lambda: provider)
    proposal = chat_actions.extract_task(REQUEST, "Africa/Lagos")
    assert proposal.title == "learn system design"
    assert proposal.due_date.isoformat() == "2026-11-15"
    assert provider.generate.call_args.args[0]["tomorrow"] == "2026-11-15"
    with pytest.raises(ValidationError):
        conversation_history.SendTurn(turn_id=uuid4(), content=REQUEST, timezone="invalid-zone")


@pytest.mark.parametrize("decision", ["approve", "reject", "goal", "roadmap"])
def test_chat_task_lifecycle_with_postgres(monkeypatch, token_verifier, access_token, decision):
    url = os.getenv("CONVERSATIONS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set CONVERSATIONS_TEST_DATABASE_URL to an isolated restricted-role test database.")
    provider = Mock()
    provider.generate.return_value = DETAILS
    monkeypatch.setattr(chat_actions, "get_planning_provider", lambda: provider)
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    headers = {"Authorization": f"Bearer {access_token(subject=str(uuid4()))}"}
    outsider = {"Authorization": f"Bearer {access_token(subject=str(uuid4()))}"}

    try:
        with psycopg.connect(url, sslmode="require", channel_binding="require") as connection:
            # The outer transaction rolls back every synthetic record. Request-level
            # transactions retain the services' normal rollback behavior via savepoints.
            connection.execute("SELECT 1")

            @contextmanager
            def storage():
                with connection.transaction():
                    yield connection

            for module in (conversation_history, private_store, records, goals):
                monkeypatch.setattr(module, "database_connection", storage)
            # The outer transaction has already started, so skip its isolation declaration.
            execute = connection.execute
            monkeypatch.setattr(connection, "execute", lambda sql, *a, **k:
                                execute("SELECT 1") if sql == "SET TRANSACTION ISOLATION LEVEL READ COMMITTED"
                                else execute(sql, *a, **k))

            try:
                with TestClient(app) as client:
                    chat = client.post(CHAT, headers=headers, json={"title": "Synthetic chat"}).json()["id"]
                    turn = {"turn_id": str(uuid4()), "content": REQUEST, "timezone": "Africa/Lagos"}
                    path = f"{CHAT}/{chat}/turns"
                    if decision in {"goal", "roadmap"}:
                        import json
                        from datetime import timedelta
                        from zoneinfo import ZoneInfo
                        today = datetime.now(ZoneInfo("Africa/Lagos")).date()
                        draft_goal = {"title": "Learn backend AI engineering", "description": "Build a portfolio", "target_date": today.replace(year=today.year + 1).isoformat()}
                        provider.generate.return_value = '{"goal":{"title":"Learn backend AI engineering","description":"Build a portfolio","target_date":"2027-05-14"}}'
                        monkeypatch.setattr(goal_plans, "get_planning_provider", lambda: provider)
                        turn["content"] = "Create a goal to learn backend AI engineering by May 14, 2027."
                        expected_date = "2027-05-14"
                        selection = {}
                        if decision == "roadmap":
                            monkeypatch.setattr(goal_plans, "personalization_enabled", lambda _: False)
                            stages = [
                                dict(milestone=f"Milestone {i}", project=f"Project {i}", deliverable="Working demo", prerequisite=None,
                                     deadline=(today + timedelta(days=i * 14)).isoformat(),
                                     tasks=[dict(title=f"Task {i}", due_date=(today + timedelta(days=i * 14 - 1)).isoformat(), hours=2)])
                                for i in (1, 2)
                            ]
                            provider.generate.return_value = json.dumps({"roadmap": {"goal": draft_goal, "weekly_hours": 4, "stages": stages}})
                            turn["content"] = f"Help me build a roadmap for AI engineering by {draft_goal['target_date']}."
                            expected_date = draft_goal["target_date"]
                            selection = {"json": {"stages": [0]}}
                            rejected = client.post(path, headers=headers, json=turn).json()["action"]
                            assert client.post(f"/api/v1/actions/{rejected['id']}/reject", headers=headers).status_code == 200
                            assert client.post(f"/api/v1/actions/{rejected['id']}/approve", headers=headers, **selection).status_code == 409
                            turn["turn_id"] = str(uuid4())
                        response = client.post(path, headers=headers, json=turn)
                        assert response.status_code == 200
                        action = response.json()["action"]
                        details = action["proposal"]["roadmap"]["goal"] if decision == "roadmap" else action["proposal"]["goal"]
                        assert details["target_date"] == expected_date
                        assert client.get("/api/v1/goals", headers=headers).json() == []
                        approval = f"/api/v1/actions/{action['id']}/approve"
                        assert client.post(approval, headers=outsider, **selection).status_code == 404
                        if decision == "roadmap":
                            assert client.post(approval, headers=headers, json={"stages": [3]}).status_code == 422
                            with monkeypatch.context() as failure:
                                failure.setattr(actions, "audit", Mock(side_effect=DatabaseError("Synthetic failure.")))
                                assert client.post(approval, headers=headers, **selection).status_code == 503
                            for domain in ("goals", "projects", "tasks"):
                                assert client.get(f"/api/v1/{domain}", headers=headers).json() == []
                        result = client.post(approval, headers=headers, **selection)
                        assert result.status_code == 200
                        assert client.post(approval, headers=headers, **selection).json() == result.json()
                        saved = client.get("/api/v1/goals", headers=headers).json()
                        assert len(saved) == 1 and saved[0]["id"] == result.json()["result_id"]
                        assert saved[0]["title"] == "Learn backend AI engineering" and not saved[0]["completed"]
                        assert client.get("/api/v1/goals", headers=outsider).json() == []
                        if decision == "roadmap":
                            receipt = result.json()["proposal"]["receipt"]
                            projects = client.get("/api/v1/projects", headers=headers).json()
                            tasks = client.get("/api/v1/tasks", headers=headers).json()
                            assert [p["id"] for p in projects] == receipt["project_ids"]
                            assert len(tasks) == 2 and all(t["goal_id"] == saved[0]["id"] and t["project_id"] == projects[0]["id"]
                                                          and t["status"] == "not_started" for t in tasks)
                            task = next(t for t in tasks if t["kind"] == "task")
                            assert [task["id"]] == receipt["task_ids"] and [task["parent_id"]] == receipt["milestone_ids"]
                            assert client.get("/api/v1/tasks", headers=outsider).json() == []
                            reloaded = client.get(f"{CHAT}/{chat}/messages", headers=headers).json()
                            assert reloaded[-1]["action"]["proposal"]["receipt"] == receipt
                        return
                    message = client.post(path, headers=headers, json=turn).json()
                    proposal = message["action"]
                    assert proposal["status"] == "pending"
                    assert proposal["proposal"]["priority"] == "high"
                    assert client.post(path, headers=headers, json=turn).json() == message
                    assert provider.generate.call_count == 1
                    assert client.get("/api/v1/tasks", headers=headers).json() == []
                    action = f"/api/v1/actions/{proposal['id']}"
                    assert client.post(f"{action}/approve", headers=outsider).status_code == 404
                    assert client.post(f"{action}/reject", headers=outsider).status_code == 404
                    assert client.get(f"{CHAT}/{chat}/messages", headers=outsider).status_code == 404

                    if decision == "approve":
                        with monkeypatch.context() as failure:
                            # Simulate failure after the INSERT, before the transaction commits.
                            def fail_audit(*args):
                                raise DatabaseError("Synthetic write failure.")

                            failure.setattr(actions, "audit", fail_audit)
                            assert client.post(f"{action}/approve", headers=headers).status_code == 503
                        assert client.get("/api/v1/tasks", headers=headers).json() == []
                        saved = client.get(f"{CHAT}/{chat}/messages", headers=headers).json()
                        assert saved[-1]["action"]["status"] == "pending"

                    response = client.post(f"{action}/{decision}", headers=headers)
                    assert response.status_code == 200
                    result = response.json()
                    assert client.post(f"{action}/{decision}", headers=headers).json() == result
                    saved = client.get(f"{CHAT}/{chat}/messages", headers=headers).json()
                    assert saved[-1]["action"] == {key: result[key] for key in ("id", "status", "result_id", "proposal")}
                    tasks = client.get("/api/v1/tasks", headers=headers).json()
                    assert client.get("/api/v1/tasks", headers=outsider).json() == []
                    if decision == "approve":
                        assert result["status"] == "applied"
                        assert len(tasks) == 1
                        assert (tasks[0]["id"], tasks[0]["title"], tasks[0]["priority"], tasks[0]["due_date"]) == (
                            result["result_id"], "learn system design", "high", "2026-11-15",
                        )
                        # The last API request set the outsider's transaction-local identity.
                        # Prove the policy hides the rows even without an owner filter.
                        assert connection.execute(
                            "SELECT id FROM public.momentum_tasks WHERE id = %s", (result["result_id"],),
                        ).fetchone() is None
                        assert connection.execute(
                            "SELECT id FROM public.momentum_actions WHERE id = %s", (proposal["id"],),
                        ).fetchone() is None
                        provider.generate.return_value = '{"search":"learn system design","field":"status","value":"completed"}'
                        edit_turn = {**turn, "turn_id": str(uuid4()), "content": "Mark my learn system design task as completed."}
                        edit_response = client.post(path, headers=headers, json=edit_turn)
                        assert edit_response.status_code == 200
                        edit = edit_response.json()["action"]
                        assert edit["proposal"]["edit"]["previous"] == "not_started"
                        edit_path = f"/api/v1/actions/{edit['id']}/approve"
                        assert client.post(edit_path, headers=outsider).status_code == 404
                        assert client.get("/api/v1/tasks", headers=headers).json()[0]["status"] == "not_started"
                        with monkeypatch.context() as failure:
                            failure.setattr(actions, "audit", Mock(side_effect=DatabaseError("Synthetic failure.")))
                            assert client.post(edit_path, headers=headers).status_code == 503
                        assert client.get("/api/v1/tasks", headers=headers).json()[0]["status"] == "not_started"
                        update = client.post(edit_path, headers=headers)
                        assert update.status_code == 200 and update.json()["result_id"] == tasks[0]["id"]
                        assert client.post(edit_path, headers=headers).json() == update.json()
                        assert client.get("/api/v1/tasks", headers=headers).json()[0]["status"] == "completed"
                        provider.generate.return_value = '{"search":"learn system design","field":"priority","value":"low"}'
                        edit_turn = {**turn, "turn_id": str(uuid4()), "content": "Change my learn system design task to low priority."}
                        next_edit = client.post(path, headers=headers, json=edit_turn).json()["action"]
                        assert client.post(f"/api/v1/actions/{next_edit['id']}/reject", headers=headers).status_code == 200
                        assert client.post(f"/api/v1/actions/{next_edit['id']}/approve", headers=headers).status_code == 409
                        assert client.get("/api/v1/tasks", headers=headers).json()[0]["priority"] == "high"
                    else:
                        assert result["status"] == "rejected"
                        assert client.post(f"{action}/approve", headers=headers).status_code == 409
                        assert tasks == []
            finally:
                connection.rollback()
    except psycopg.Error:
        pytest.fail("Restricted PostgreSQL chat action check failed. Verify the test database and grants.", pytrace=False)
