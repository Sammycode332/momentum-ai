from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Response
from psycopg import Connection
from psycopg.rows import class_row
from pydantic import BaseModel, ConfigDict, StrictBool, StringConstraints, field_validator, model_validator

from app.api_errors import ApiError
from app.auth import AuthenticatedPrincipal, require_authenticated_principal
from app.database import DatabaseConfigurationError, DatabaseError, database_connection

router = APIRouter(prefix="/api/v1/goals", tags=["goals"])
Principal = Annotated[AuthenticatedPrincipal, Depends(require_authenticated_principal)]


class GoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]

    @field_validator("title")
    @classmethod
    def reject_null_character(cls, title: str) -> str:
        if "\0" in title:
            raise ValueError("A goal title cannot contain a null character.")
        return title


class Goal(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    completed: bool = False


class GoalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200, pattern=r"^[^\x00]+$")] | None = None
    completed: StrictBool | None = None

    @model_validator(mode="after")
    def require_update(self):
        if not self.model_fields_set or any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Provide a title or completion state; null is not allowed.")
        return self


@contextmanager
def goals_connection(owner: str) -> Iterator[Connection]:
    try:
        with database_connection() as connection:
            active = connection.execute(
                "SELECT pg_catalog.row_security_active('public.momentum_goals'::regclass)"
            ).fetchone()
            if active != (True,):
                raise DatabaseError("Goals require an RLS-constrained database role.")
            connection.execute(
                "SELECT pg_catalog.set_config('momentum.user_id', %s, true)", (owner,)
            )
            yield connection
    except (DatabaseConfigurationError, DatabaseError):
        raise ApiError(503, "GOALS_UNAVAILABLE", "Goals are temporarily unavailable.") from None


@router.get("")
def list_goals(principal: Principal, response: Response) -> list[Goal]:
    response.headers["Cache-Control"] = "no-store"
    with goals_connection(principal.subject) as connection:
        with connection.cursor(row_factory=class_row(Goal)) as cursor:
            cursor.execute(
                """
                SELECT id, title, created_at, completed FROM public.momentum_goals
                WHERE owner_id = %s ORDER BY created_at DESC, id DESC
                """,
                (principal.subject,),
            )
            return cursor.fetchall()


@router.post("", status_code=201)
def create_goal(body: GoalCreate, principal: Principal, response: Response) -> Goal:
    response.headers["Cache-Control"] = "no-store"
    with goals_connection(principal.subject) as connection:
        with connection.cursor(row_factory=class_row(Goal)) as cursor:
            return insert_goal(cursor, principal.subject, body)


def insert_goal(cursor, owner: str, goal: GoalCreate):
    cursor.execute(
        """INSERT INTO public.momentum_goals (id, owner_id, title)
        VALUES (%s, %s, %s) RETURNING id, title, created_at, completed""",
        (uuid4(), owner, goal.title),
    )
    saved = cursor.fetchone()
    if saved is None:
        raise DatabaseError("The goal insert returned no row.")
    return saved


@router.patch("/{goal_id}")
def update_goal(goal_id: UUID, body: GoalUpdate, principal: Principal, response: Response) -> Goal:
    response.headers["Cache-Control"] = "no-store"
    with goals_connection(principal.subject) as connection:
        with connection.cursor(row_factory=class_row(Goal)) as cursor:
            cursor.execute(
                """UPDATE public.momentum_goals
                   SET title = COALESCE(%s, title), completed = COALESCE(%s, completed)
                   WHERE id = %s AND owner_id = %s
                   RETURNING id, title, created_at, completed""",
                (body.title, body.completed, goal_id, principal.subject),
            )
            goal = cursor.fetchone()
            if goal is None:
                raise ApiError(404, "GOAL_NOT_FOUND", "Goal not found.")
            return goal


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: UUID, principal: Principal) -> Response:
    with goals_connection(principal.subject) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM public.momentum_goals WHERE id = %s AND owner_id = %s",
                (goal_id, principal.subject),
            )
            if cursor.rowcount != 1:
                raise ApiError(404, "GOAL_NOT_FOUND", "Goal not found.")
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
