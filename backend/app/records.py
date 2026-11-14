from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Response
from psycopg import Connection
from psycopg.rows import dict_row
from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError, field_validator

from app.api_errors import ApiError
from app.auth import AuthenticatedPrincipal, require_authenticated_principal
from app.database import DatabaseConfigurationError, DatabaseError, database_connection

router = APIRouter(prefix="/api/v1", tags=["records"])
Principal = Annotated[AuthenticatedPrincipal, Depends(require_authenticated_principal)]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Description = Annotated[str, StringConstraints(max_length=4000)]
Status = Literal["not_started", "in_progress", "completed", "paused"]


class RecordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def reject_null_text(cls, value):
        if isinstance(value, str) and "\0" in value:
            raise ValueError("Text cannot contain a null character.")
        return value


class ProjectInput(RecordInput):
    name: Text
    description: Description | None = None
    status: Status = "not_started"
    deadline: date | None = None


class TaskInput(RecordInput):
    model_config = ConfigDict(extra="forbid")
    title: Text
    description: Description | None = None
    status: Status = "not_started"
    priority: Literal["low", "medium", "high"] = "medium"
    due_date: date | None = None
    project_id: UUID | None = None
    goal_id: UUID | None = None
    parent_id: UUID | None = None
    kind: Literal['task','milestone'] = 'task'


class LearningInput(RecordInput):
    model_config = ConfigDict(extra="forbid")
    subject: Text
    objective: LongText
    progress_status: Status = "not_started"


class AcademicInput(RecordInput):
    model_config = ConfigDict(extra="forbid")
    activity: Text
    description: Description | None = None
    status: Status = "not_started"
    deadline: date | None = None


class OpportunityInput(RecordInput):
    model_config = ConfigDict(extra="forbid")
    name: Text
    type: Text
    status: Status = "not_started"
    application_stage: Literal['saved','preparing','applied','interviewing','offered','accepted','rejected','withdrawn'] = 'saved'
    application_deadline: date | None = None
    url: str | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is not None and (len(value) > 2048 or not value.startswith(("https://", "http://"))):
            raise ValueError("Opportunity URL must be an HTTP(S) URL.")
        return value


class Record(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    name: str | None = None
    title: str | None = None
    subject: str | None = None
    activity: str | None = None
    description: str | None = None
    status: str | None = None
    deadline: date | None = None
    priority: str | None = None
    due_date: date | None = None
    project_id: UUID | None = None
    objective: str | None = None
    goal_id: UUID | None = None
    parent_id: UUID | None = None
    kind: str | None = None
    progress_status: str | None = None
    type: str | None = None
    application_deadline: date | None = None
    application_stage: str | None = None
    url: str | None = None


TABLES = {
    "projects": ("momentum_projects", ProjectInput),
    "tasks": ("momentum_tasks", TaskInput),
    "learning": ("momentum_learning", LearningInput),
    "academics": ("momentum_academics", AcademicInput),
    "opportunities": ("momentum_opportunities", OpportunityInput),
}


@contextmanager
def records_connection(owner: str) -> Iterator[Connection]:
    try:
        with database_connection() as connection:
            active = connection.execute(
                """SELECT bool_and(pg_catalog.row_security_active(table_name::regclass))
                FROM unnest(ARRAY['public.momentum_projects', 'public.momentum_tasks',
                'public.momentum_learning', 'public.momentum_academics',
                'public.momentum_opportunities']) AS table_name"""
            ).fetchone()
            if active != (True,):
                raise DatabaseError("Records require an RLS-constrained database role.")
            connection.execute("SELECT pg_catalog.set_config('momentum.user_id', %s, true)", (owner,))
            yield connection
    except (DatabaseConfigurationError, DatabaseError):
        raise ApiError(503, "RECORDS_UNAVAILABLE", "Records are temporarily unavailable.") from None


def _table(domain: str) -> str:
    if domain not in TABLES:
        raise ApiError(404, "NOT_FOUND", "The requested record type was not found.")
    return TABLES[domain][0]


def _body(domain: str, payload: dict[str, Any]) -> BaseModel:
    try:
        return TABLES[domain][1](**payload)
    except ValidationError as error:
        raise ApiError(422, "INVALID_REQUEST", "Check the request fields and try again.") from error


def _record(connection: Connection, table: str, owner: str, record_id: UUID) -> dict[str, Any] | None:
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(f"SELECT * FROM public.{table} WHERE id = %s AND owner_id = %s", (record_id, owner))
        return cursor.fetchone()


def validate_task_links(connection, owner, body, record_id=None):
    # Serialize relationship changes per owner to prevent concurrent cycles.
    connection.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', (owner,))
    if body.get('goal_id'):
        if connection.execute("SELECT row_security_active('public.momentum_goals'::regclass)").fetchone() != (True,):
            raise DatabaseError('Goal RLS required')
        if _record(connection,'momentum_goals',owner,body['goal_id']) is None:
            raise ApiError(422,'INVALID_GOAL','Choose one of your own goals.')
    if body.get('parent_id'):
        parent = _record(connection,'momentum_tasks',owner,body['parent_id'])
        if parent is None or parent['id'] == record_id or parent.get('parent_id') is not None:
            raise ApiError(422,'INVALID_PARENT','Choose one of your own top-level tasks.')
        if parent.get('project_id') != body.get('project_id'):
            raise ApiError(422,'INVALID_PARENT','A subtask must belong to the same project as its parent.')
    if record_id:
        children = connection.execute('SELECT project_id FROM momentum_tasks WHERE parent_id=%s AND owner_id=%s',(record_id,owner)).fetchall()
        if children and (body.get('parent_id') or any(p[0] != body.get('project_id') for p in children)):
            raise ApiError(422,'TASK_HAS_CHILDREN','Move or detach the subtasks before changing this relationship.')


@router.get("/{domain}")
def list_records(domain: str, principal: Principal, response: Response) -> list[dict[str, Any]]:
    response.headers["Cache-Control"] = "no-store"
    table = _table(domain)
    with records_connection(principal.subject) as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(f"SELECT * FROM public.{table} WHERE owner_id = %s ORDER BY updated_at DESC, id DESC", (principal.subject,))
            return cursor.fetchall()


@router.post("/{domain}", status_code=201)
def create_record(domain: str, payload: dict[str, Any], principal: Principal, response: Response) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    table = _table(domain)
    body = _body(domain, payload).model_dump()
    with records_connection(principal.subject) as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            if domain == "tasks":
                return insert_task(cursor, principal.subject, TaskInput.model_validate(body))
            return insert_record(cursor, table, principal.subject, body)


def insert_record(cursor, table, owner, body):
    columns = ["id", "owner_id", *body.keys()]
    values = [uuid4(), owner, *body.values()]
    placeholders = ", ".join(["%s"] * len(values))
    return cursor.execute(
        f"INSERT INTO public.{table} ({', '.join(columns)}) VALUES ({placeholders}) RETURNING *", values,
    ).fetchone()


def insert_task(cursor, owner: str, task: TaskInput):
    connection = cursor.connection
    body = task.model_dump()
    if task.project_id is not None:
        if _record(connection, "momentum_projects", owner, task.project_id) is None:
            raise ApiError(422, "INVALID_PROJECT", "Choose one of your own projects.")
    validate_task_links(connection, owner, body)
    return insert_record(cursor, "momentum_tasks", owner, body)


@router.put("/{domain}/{record_id}")
def update_record(domain: str, record_id: UUID, payload: dict[str, Any], principal: Principal, response: Response) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    table = _table(domain)
    body = _body(domain, payload).model_dump()
    with records_connection(principal.subject) as connection:
        if domain == "tasks" and body.get("project_id") is not None:
            if _record(connection, "momentum_projects", principal.subject, body["project_id"]) is None:
                raise ApiError(422, "INVALID_PROJECT", "Choose one of your own projects.")
        if domain == 'tasks':
            validate_task_links(connection,principal.subject,body,record_id)
        with connection.cursor(row_factory=dict_row) as cursor:
            saved = write_record_update(cursor, table, principal.subject, record_id, body)
    if saved is None:
        raise ApiError(404, "NOT_FOUND", "The requested record was not found.")
    return saved


def write_record_update(cursor, table, owner, record_id, body):
    # Both table and columns come from server-owned mappings or validated input models.
    assignments = ", ".join(f"{column} = %s" for column in body)
    return cursor.execute(
        f"UPDATE public.{table} SET {assignments}, updated_at = now() WHERE id = %s AND owner_id = %s RETURNING *",
        (*body.values(), record_id, owner),
    ).fetchone()


@router.delete("/{domain}/{record_id}", status_code=204)
def delete_record(domain: str, record_id: UUID, principal: Principal, response: Response) -> Response:
    table = _table(domain)
    with records_connection(principal.subject) as connection:
        result = connection.execute(
            f"DELETE FROM public.{table} WHERE id = %s AND owner_id = %s", (record_id, principal.subject)
        )
    if result.rowcount != 1:
        raise ApiError(404, "NOT_FOUND", "The requested record was not found.")
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
