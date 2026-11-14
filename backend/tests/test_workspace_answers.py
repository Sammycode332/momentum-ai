import os
from contextlib import nullcontext
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from app import conversation, private_store, workspace_answers
from app.auth import get_token_verifier
from app.auth import AuthenticatedPrincipal
from app import conversation_history
from app.main import app

QUERIES = [
    ("What tasks do I have today?", "today"),
    ("Show my unfinished tasks.", "unfinished"),
    ("What deadlines are coming up?", "deadlines"),
    ("How am I progressing toward my goals?", "goals"),
    ("Which projects need my attention?", "projects"),
]


@pytest.mark.parametrize(("question", "intent"), QUERIES)
def test_signed_workspace_lookups_skip_provider(monkeypatch, token_verifier, access_token, question, intent):
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    answer = Mock(return_value="Saved workspace summary.")
    monkeypatch.setattr(conversation, "workspace_answer", answer)
    monkeypatch.setattr(conversation, "get_planning_provider", Mock(side_effect=AssertionError))
    with TestClient(app) as client:
        message = {"messages": [{"role": "user", "content": question}]}
        assert client.post("/api/v1/ai/chat", json=message).status_code == 401
        assert client.post("/api/v1/ai/chat", json=message, headers={
            "Authorization": f"Bearer {access_token()}",
        }).json()["reply"] == "Saved workspace summary."
    answer.assert_called_once_with(intent, "test-user-a", "UTC")


def test_workspace_answers_use_real_isolated_records(monkeypatch):
    url = os.getenv("CONVERSATIONS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set CONVERSATIONS_TEST_DATABASE_URL to an isolated restricted-role database.")
    class Clock(datetime):
        @classmethod
        def now(cls, tz):
            return cls(2026, 11, 13, 23, 45, tzinfo=UTC)

    monkeypatch.setattr(workspace_answers, "datetime", Clock)
    owner, other, goal, project = str(uuid4()), str(uuid4()), uuid4(), uuid4()
    with psycopg.connect(url, connect_timeout=5) as connection:
        monkeypatch.setattr(private_store, "database_connection", lambda: nullcontext(connection))
        try:
            connection.execute("SELECT set_config('momentum.user_id', %s, true)", (other,))
            connection.execute("INSERT INTO momentum_tasks (id,owner_id,title,status,priority,due_date) VALUES (%s,%s,'Other task','not_started','medium','2026-11-14')",
                               (uuid4(), other))
            connection.execute("SELECT set_config('momentum.user_id', %s, true)", (owner,))
            connection.execute("INSERT INTO momentum_goals (id,owner_id,title) VALUES (%s,%s,'Study goal')", (goal, owner))
            connection.execute("INSERT INTO momentum_projects (id,owner_id,name,status) VALUES (%s,%s,'Study project','not_started')", (project, owner))
            for title, status, due in [("Today task", "not_started", "2026-11-14"),
                                       ("Earlier task", "in_progress", "2026-11-13"),
                                       ("Finished task", "completed", "2026-11-15")]:
                connection.execute(
                    """INSERT INTO momentum_tasks(id,owner_id,title,status,priority,due_date,goal_id,project_id)
                    VALUES (%s,%s,%s,%s,'medium',%s,%s,%s)""", (uuid4(), owner, title, status, due, goal, project),
                )
            answers = {intent: workspace_answers.workspace_answer(intent, owner, "Africa/Lagos")
                       for _, intent in QUERIES}
            assert all("Other task" not in answer for answer in answers.values())
            assert "Today task" in answers["today"] and "Earlier task" not in answers["today"]
            assert "Earlier task" in answers["unfinished"] and "Finished task" not in answers["unfinished"]
            assert "Today task" in answers["deadlines"] and "Finished task" not in answers["deadlines"]
            assert "1 of 3 linked tasks complete" in answers["goals"]
            assert "Study project" in answers["projects"] and "1 overdue" in answers["projects"]
            detail = workspace_answers.workspace_answer("milestones", owner, "Africa/Lagos")
            assert "Finished task · task · completed" in detail and "Earlier task · task · in progress" in detail
            assert "No saved records" in workspace_answers.workspace_answer("goals", other, "Africa/Lagos")
        finally:
            connection.rollback()


def test_saved_chat_uses_the_request_timezone_without_a_proposal(monkeypatch):
    turn = conversation_history.SendTurn(turn_id=uuid4(), timezone="Africa/Lagos", content=QUERIES[0][0])
    stored_user = {"role": "user", "content": turn.content, "position": 1}
    monkeypatch.setattr(conversation_history, "owned_cursor", lambda owner: nullcontext(object()))
    monkeypatch.setattr(conversation_history, "require_conversation", Mock())
    monkeypatch.setattr(conversation_history, "touch", Mock())
    monkeypatch.setattr(conversation_history, "turn_rows", Mock(side_effect=[{}, {"user": stored_user}]))
    monkeypatch.setattr(conversation_history, "recent_messages", Mock(return_value=[]))
    insert = Mock(return_value={"content": "Saved results"})
    monkeypatch.setattr(conversation_history, "insert_message", insert)
    answer = Mock(return_value="Saved results")
    monkeypatch.setattr(conversation_history, "workspace_answer", answer)
    write = Mock(side_effect=AssertionError)
    monkeypatch.setattr(conversation_history, "save_proposal", write)
    result = conversation_history.send_turn(uuid4(), turn, AuthenticatedPrincipal("owner"))
    answer.assert_called_once_with("today", "owner", "Africa/Lagos")
    write.assert_not_called()
    assert result == {"content": "Saved results"}
