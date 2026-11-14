from contextlib import contextmanager
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Query
from psycopg.errors import LockNotAvailable
from psycopg.rows import dict_row
from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.actions import Proposal, save_proposal
from app.api_errors import ApiError
from app.chat_actions import (
    PENDING, TASK_PENDING, TASK_EDIT_REQUEST, TASK_REQUEST, UNSUPPORTED, WRITE_REQUEST,
    extract_task, extract_task_edit, proposal_id, safe_chat_reply,
)
from app.conversation import ChatRequest, MessageText, Turn, generate_reply
from app.database import DatabaseConfigurationError, DatabaseError, database_connection
from app.planning import Principal
from app.workspace_answers import workspace_answer, workspace_intent
from app.goal_plans import GOAL_REQUEST, ROADMAP_REQUEST, draft_goal

router = APIRouter(prefix="/api/v1/ai/conversations", tags=["conversation history"])
CONVERSATIONS = "public.momentum_conversations"
MESSAGES = "public.momentum_conversation_messages"
SUMMARY = "id, title, updated_at"
MESSAGE = "turn_id, position, role, content"


class TitleInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120, pattern=r"^[^\x00]+$")]


class Conversation(TitleInput):
    id: UUID
    updated_at: datetime


class ChatAction(BaseModel):
    id: UUID
    proposal: Proposal
    status: Literal["pending", "applied", "rejected"]
    result_id: UUID | None


class Message(BaseModel):
    turn_id: UUID
    position: int
    role: Literal["user", "assistant"]
    content: str
    action: ChatAction | None = None


class SendTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    turn_id: UUID
    content: MessageText
    timezone: Annotated[str, StringConstraints(min_length=1, max_length=64)] = "UTC"

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, timezone: str) -> str:
        try:
            ZoneInfo(timezone)
        except (ValueError, ZoneInfoNotFoundError):
            raise ValueError("Use an IANA timezone.") from None
        return timezone


def require_action_rls(cursor, *extra_tables):
    tables = ("momentum_actions", *extra_tables)
    active = cursor.execute(
        """SELECT bool_and(row_security_active(table_name::regclass)) AS active
        FROM unnest(%s::text[]) AS t(table_name)""",
        ([f"public.{table}" for table in tables],),
    ).fetchone()
    if not active or active["active"] is not True:
        raise DatabaseError("Chat actions require RLS.")


def restore_messages(cursor, owner, chat_id, messages):
    links = {
        row["turn_id"]: proposal_id(owner, chat_id, row["turn_id"])
        for row in messages if row["role"] == "assistant" and row["content"] in {PENDING, TASK_PENDING}
    }
    actions = {}
    if links:
        require_action_rls(cursor)
        rows = cursor.execute(
            """SELECT id, proposal, status, result_id FROM public.momentum_actions
            WHERE owner_id = %s AND id = ANY(%s)""",
            (owner, list(links.values())),
        ).fetchall()
        actions = {row["id"]: row for row in rows}

    restored = []
    for row in messages:
        if row["role"] == "user":
            restored.append(row)
        elif row["turn_id"] in links:
            action = actions.get(links[row["turn_id"]])
            restored.append({**row, "action": action} if action else {**row, "content": "This proposal is unavailable."})
        else:
            restored.append({**row, "content": safe_chat_reply(row["content"])})
    return restored


@contextmanager
def owned_cursor(owner: str):
    try:
        with database_connection() as connection:
            connection.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
            if connection.execute(
                """SELECT row_security_active('public.momentum_conversations'::regclass),
                          row_security_active('public.momentum_conversation_messages'::regclass)"""
            ).fetchone() != (True, True):
                raise DatabaseError("Conversation storage requires RLS.")
            connection.execute("SELECT set_config('momentum.user_id', %s, true)", (owner,))
            with connection.cursor(row_factory=dict_row) as cursor:
                try:
                    yield cursor
                except LockNotAvailable:
                    raise ApiError(409, "CONVERSATION_BUSY", "A reply is being generated. Try again shortly.") from None
    except (DatabaseConfigurationError, DatabaseError):
        raise ApiError(503, "CONVERSATIONS_UNAVAILABLE", "Conversation storage is unavailable.") from None


def require_conversation(cursor, owner: str, chat_id: UUID, *, lock: bool = False):
    suffix = " FOR UPDATE NOWAIT" if lock else ""
    row = cursor.execute(
        f"SELECT {SUMMARY} FROM {CONVERSATIONS} WHERE owner_id = %s AND id = %s{suffix}",
        (owner, chat_id),
    ).fetchone()
    if row is None:
        raise ApiError(404, "CONVERSATION_NOT_FOUND", "Conversation not found.")
    return row


def recent_messages(cursor, owner: str, chat_id: UUID, limit: int):
    return list(reversed(cursor.execute(
        f"""SELECT {MESSAGE} FROM {MESSAGES} WHERE owner_id = %s AND conversation_id = %s
        ORDER BY position DESC, role ASC LIMIT %s""", (owner, chat_id, limit),
    ).fetchall()))


@router.get("")
def list_conversations(principal: Principal) -> list[Conversation]:
    with owned_cursor(principal.subject) as cursor:
        return cursor.execute(
            f"SELECT {SUMMARY} FROM {CONVERSATIONS} WHERE owner_id = %s ORDER BY updated_at DESC, id DESC LIMIT 50",
            (principal.subject,),
        ).fetchall()


@router.post("", status_code=201)
def create_conversation(body: TitleInput, principal: Principal) -> Conversation:
    with owned_cursor(principal.subject) as cursor:
        return cursor.execute(
            f"INSERT INTO {CONVERSATIONS} (id, owner_id, title) VALUES (%s, %s, %s) RETURNING {SUMMARY}",
            (uuid4(), principal.subject, body.title),
        ).fetchone()


@router.get("/{chat_id}/messages")
def get_messages(
    chat_id: UUID, principal: Principal, limit: Annotated[int, Query(ge=1, le=100)] = 60,
) -> list[Message]:
    with owned_cursor(principal.subject) as cursor:
        require_conversation(cursor, principal.subject, chat_id)
        rows = recent_messages(cursor, principal.subject, chat_id, limit)
        return restore_messages(cursor, principal.subject, chat_id, rows)


@router.patch("/{chat_id}")
def rename_conversation(chat_id: UUID, body: TitleInput, principal: Principal) -> Conversation:
    with owned_cursor(principal.subject) as cursor:
        require_conversation(cursor, principal.subject, chat_id, lock=True)
        return cursor.execute(
            f"UPDATE {CONVERSATIONS} SET title = %s WHERE owner_id = %s AND id = %s RETURNING {SUMMARY}",
            (body.title, principal.subject, chat_id),
        ).fetchone()


@router.delete("/{chat_id}", status_code=204)
def delete_conversation(chat_id: UUID, principal: Principal) -> None:
    with owned_cursor(principal.subject) as cursor:
        require_conversation(cursor, principal.subject, chat_id, lock=True)
        cursor.execute(f"DELETE FROM {CONVERSATIONS} WHERE owner_id = %s AND id = %s",
                       (principal.subject, chat_id))


def insert_message(cursor, owner, chat_id, turn_id, position, role, content):
    return cursor.execute(
        f"""INSERT INTO {MESSAGES} (owner_id, conversation_id, turn_id, position, role, content)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING {MESSAGE}""",
        (owner, chat_id, turn_id, position, role, content),
    ).fetchone()


def turn_rows(cursor, owner, chat_id, turn_id):
    return {row["role"]: row for row in cursor.execute(
        f"""SELECT {MESSAGE} FROM {MESSAGES}
        WHERE owner_id = %s AND conversation_id = %s AND turn_id = %s""",
        (owner, chat_id, turn_id),
    ).fetchall()}


def touch(cursor, owner, chat_id):
    cursor.execute(f"UPDATE {CONVERSATIONS} SET updated_at = now() WHERE owner_id = %s AND id = %s",
                   (owner, chat_id))


def bounded_history(rows) -> ChatRequest:
    turns = [Turn(role=row["role"], content=row["content"]) for row in rows]
    if turns and turns[0].role == "assistant":
        turns = turns[1:]
    while sum(len(turn.content) for turn in turns) > 16000:
        turns = turns[2:]
    return ChatRequest(messages=turns)


@router.post("/{chat_id}/turns")
def send_turn(chat_id: UUID, body: SendTurn, principal: Principal) -> Message:
    owner = principal.subject
    if "\0" in body.content:
        raise ApiError(422, "INVALID_REQUEST", "Check the message and try again.")
    # Commit the user turn independently, so failures leave a recoverable message.
    with owned_cursor(owner) as cursor:
        require_conversation(cursor, owner, chat_id, lock=True)
        saved = turn_rows(cursor, owner, chat_id, body.turn_id)
        if saved:
            if saved["user"]["content"] != body.content:
                raise ApiError(409, "TURN_CONFLICT", "This turn ID already belongs to a different message.")
            if "assistant" in saved:
                return restore_messages(cursor, owner, chat_id, [saved["assistant"]])[0]
        else:
            latest = recent_messages(cursor, owner, chat_id, 1)
            if latest and latest[0]["role"] == "user":
                raise ApiError(409, "TURN_PENDING", "Retry the last message before sending a new one.")
            position = latest[0]["position"] + 1 if latest else 1
            insert_message(cursor, owner, chat_id, body.turn_id, position, "user", body.content)
            touch(cursor, owner, chat_id)

    with owned_cursor(owner) as cursor:
        require_conversation(cursor, owner, chat_id, lock=True)
        saved = turn_rows(cursor, owner, chat_id, body.turn_id)
        if "assistant" in saved:
            return restore_messages(cursor, owner, chat_id, [saved["assistant"]])[0]
        action = None
        if TASK_REQUEST.search(body.content):
            task = extract_task(body.content, body.timezone)
            if task is None:
                content = (
                    "What should the task be called, and does it have a due date? "
                    "Reply with one task request that includes those details."
                )
            else:
                require_action_rls(cursor, "momentum_audit")
                action = save_proposal(cursor, owner, task, proposal_id=proposal_id(owner, chat_id, body.turn_id))
                content = PENDING
        elif TASK_EDIT_REQUEST.search(body.content):
            require_action_rls(cursor, "momentum_audit", "momentum_tasks", "momentum_projects")
            content, task = extract_task_edit(cursor, owner, body.content, body.timezone)
            if task:
                action = save_proposal(cursor, owner, task, proposal_id=proposal_id(owner, chat_id, body.turn_id))
        elif GOAL_REQUEST.search(body.content) or ROADMAP_REQUEST.search(body.content):
            is_roadmap = bool(ROADMAP_REQUEST.search(body.content))
            require_action_rls(cursor, "momentum_audit", "momentum_goals")
            draft = draft_goal(cursor, owner, body.content, body.timezone, roadmap=is_roadmap)
            if draft is None:
                content = ("What do you want to achieve, and by when? Include both in your roadmap request."
                           if is_roadmap else "What outcome would you like to save as a goal? Repeat the goal request with that outcome.")
            else:
                proposal = Proposal(
                    kind="save_roadmap" if is_roadmap else "create_goal",
                    title=draft.goal.title if is_roadmap else draft.title, reason="Requested in chat.",
                    roadmap=draft if is_roadmap else None, goal=None if is_roadmap else draft,
                )
                action = save_proposal(cursor, owner, proposal, proposal_id=proposal_id(owner, chat_id, body.turn_id))
                content = PENDING
        elif WRITE_REQUEST.search(body.content):
            content = UNSUPPORTED
        elif intent := workspace_intent(body.content):
            content = workspace_answer(intent, owner, body.timezone)
        else:
            history = bounded_history(recent_messages(cursor, owner, chat_id, 9))
            content = generate_reply(history, owner).reply
            if content in {PENDING, TASK_PENDING}:
                content = UNSUPPORTED
        if "\0" in content:
            raise ApiError(502, "AI_INVALID_REPLY", "Gemini returned an unreadable reply. Try again.")
        result = insert_message(cursor, owner, chat_id, body.turn_id, saved["user"]["position"],
                                "assistant", content)
        touch(cursor, owner, chat_id)
        return {**result, "action": action} if action else result
