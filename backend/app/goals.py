from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Response
from psycopg import Connection
from psycopg.rows import class_row
from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

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
                SELECT id, title, created_at FROM public.momentum_goals
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
            cursor.execute(
                """
                INSERT INTO public.momentum_goals (id, owner_id, title)
                VALUES (%s, %s, %s) RETURNING id, title, created_at
                """,
                (uuid4(), principal.subject, body.title),
            )
            goal = cursor.fetchone()
            if goal is None:
                raise DatabaseError("The goal insert returned no row.")
            return goal
