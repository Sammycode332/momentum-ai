import os
from contextlib import contextmanager
from unittest.mock import Mock
from uuid import uuid4

import psycopg
import pytest

from app import conversation_history as history
from app.api_errors import ApiError
from app.auth import AuthenticatedPrincipal
from app.conversation import ChatReply


def test_failed_turn_is_retried_once_and_continuation_uses_saved_history(monkeypatch):
    rows = []

    @contextmanager
    def cursor(owner):
        assert owner == "test-owner"
        yield None

    def insert(_, owner, chat, turn_id, position, role, content):
        assert owner == "test-owner"
        row = dict(turn_id=turn_id, position=position, role=role, content=content)
        rows.append(row)
        return row

    monkeypatch.setattr(history, "owned_cursor", cursor)
    monkeypatch.setattr(history, "require_conversation", Mock())
    monkeypatch.setattr(history, "touch", Mock())
    monkeypatch.setattr(history, "recent_messages", lambda _, owner, chat, limit: rows[-limit:])
    monkeypatch.setattr(history, "turn_rows", lambda _, owner, chat, turn_id: {
        row["role"]: row for row in rows if row["turn_id"] == turn_id
    })
    monkeypatch.setattr(history, "insert_message", insert)
    generate = Mock(side_effect=[
        ApiError(502, "TEST_FAILURE", "Synthetic failure"),
        ChatReply(reply="First answer"), ChatReply(reply="Follow-up answer"),
    ])
    monkeypatch.setattr(history, "generate_reply", generate)
    principal, chat_id = AuthenticatedPrincipal("test-owner"), uuid4()
    first = history.SendTurn(turn_id=uuid4(), content="First question")
    with pytest.raises(ApiError):
        history.send_turn(chat_id, first, principal)
    assert [row["role"] for row in rows] == ["user"]
    reply = history.send_turn(chat_id, first, principal)
    assert history.send_turn(chat_id, first, principal) == reply
    assert generate.call_count == 2
    with pytest.raises(ApiError) as conflict:
        history.send_turn(chat_id, first.model_copy(update={"content": "Changed"}), principal)
    assert conflict.value.code == "TURN_CONFLICT"
    history.send_turn(chat_id, history.SendTurn(turn_id=uuid4(), content="Follow-up"), principal)
    assert [turn.content for turn in generate.call_args.args[0].messages] == [
        "First question", "First answer", "Follow-up",
    ]
    assert [row["position"] for row in rows] == [1, 1, 2, 2]


def test_conversation_lookup_hides_other_owners():
    cursor = Mock()
    cursor.execute.return_value.fetchone.return_value = None
    chat_id = uuid4()
    with pytest.raises(ApiError) as failure:
        history.require_conversation(cursor, "other-user", chat_id)
    assert failure.value.status_code == 404
    assert cursor.execute.call_args.args[1] == ("other-user", chat_id)


def test_postgres_conversation_rls_and_delete_cascade():
    url = os.getenv("CONVERSATIONS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set CONVERSATIONS_TEST_DATABASE_URL to an isolated database with migration 004 and grants.")
    owner, other, chat_id = str(uuid4()), str(uuid4()), uuid4()
    try:
        with psycopg.connect(url) as connection:
            try:
                assert connection.execute(
                    "SELECT row_security_active(%s::regclass), row_security_active(%s::regclass)",
                    (history.CONVERSATIONS, history.MESSAGES),
                ).fetchone() == (True, True)
                connection.execute("SELECT set_config('momentum.user_id', %s, true)", (owner,))
                connection.execute(f"INSERT INTO {history.CONVERSATIONS} (id, owner_id, title) VALUES (%s, %s, 'Synthetic')",
                                   (chat_id, owner))
                connection.execute(f"""INSERT INTO {history.MESSAGES}
                    (conversation_id, owner_id, turn_id, position, role, content) VALUES (%s, %s, %s, 1, 'user', 'Synthetic')""",
                    (chat_id, owner, uuid4()))
                connection.execute("SELECT set_config('momentum.user_id', %s, true)", (other,))
                assert connection.execute(f"SELECT id FROM {history.CONVERSATIONS} WHERE id = %s", (chat_id,)).fetchone() is None
                assert connection.execute(f"SELECT content FROM {history.MESSAGES} WHERE conversation_id = %s", (chat_id,)).fetchone() is None
                assert connection.execute(f"DELETE FROM {history.CONVERSATIONS} WHERE id = %s", (chat_id,)).rowcount == 0
                connection.execute("SELECT set_config('momentum.user_id', %s, true)", (owner,))
                assert connection.execute(f"DELETE FROM {history.CONVERSATIONS} WHERE id = %s", (chat_id,)).rowcount == 1
                assert connection.execute(f"SELECT content FROM {history.MESSAGES} WHERE conversation_id = %s", (chat_id,)).fetchone() is None
            finally:
                connection.rollback()
    except psycopg.Error:
        pytest.fail("PostgreSQL conversation policy check failed. Verify the test migration and role.", pytrace=False)
