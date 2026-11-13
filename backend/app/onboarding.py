from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response
from psycopg import Connection
from psycopg.rows import class_row
from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.api_errors import ApiError
from app.auth import AuthenticatedPrincipal, require_authenticated_principal
from app.database import DatabaseConfigurationError, DatabaseError, database_connection

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])
Principal = Annotated[AuthenticatedPrincipal, Depends(require_authenticated_principal)]


class Preferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_focus: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    current_goals: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    planning_time: Annotated[str, StringConstraints(pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")]

    @field_validator("primary_focus", "current_goals")
    @classmethod
    def reject_null_character(cls, value: str) -> str:
        if "\0" in value:
            raise ValueError("Onboarding text cannot contain a null character.")
        return value


class Onboarding(BaseModel):
    status: Literal["completed", "skipped"]
    primary_focus: str | None
    current_goals: str | None
    planning_time: str | None


@contextmanager
def onboarding_connection(owner: str) -> Iterator[Connection]:
    try:
        with database_connection() as connection:
            active = connection.execute(
                "SELECT pg_catalog.row_security_active('public.momentum_onboarding'::regclass)"
            ).fetchone()
            if active != (True,):
                raise DatabaseError("Onboarding requires an RLS-constrained database role.")
            connection.execute(
                "SELECT pg_catalog.set_config('momentum.user_id', %s, true)", (owner,)
            )
            yield connection
    except (DatabaseConfigurationError, DatabaseError):
        raise ApiError(503, "ONBOARDING_UNAVAILABLE", "Onboarding is temporarily unavailable.") from None


def read_onboarding(connection: Connection, owner: str) -> Onboarding | None:
    with connection.cursor(row_factory=class_row(Onboarding)) as cursor:
        cursor.execute(
            """
            SELECT status, primary_focus, current_goals, planning_time
            FROM public.momentum_onboarding WHERE owner_id = %s
            """,
            (owner,),
        )
        return cursor.fetchone()


@router.get("")
def get_onboarding(principal: Principal, response: Response) -> Onboarding | None:
    response.headers["Cache-Control"] = "no-store"
    with onboarding_connection(principal.subject) as connection:
        return read_onboarding(connection, principal.subject)


@router.put("")
def save_onboarding(body: Preferences, principal: Principal, response: Response) -> Onboarding:
    response.headers["Cache-Control"] = "no-store"
    with onboarding_connection(principal.subject) as connection:
        connection.execute(
            """
            INSERT INTO public.momentum_onboarding AS profile
                (owner_id, status, primary_focus, current_goals, planning_time)
            VALUES (%s, 'completed', %s, %s, %s)
            ON CONFLICT (owner_id) DO UPDATE
            SET status = EXCLUDED.status, primary_focus = EXCLUDED.primary_focus,
                current_goals = EXCLUDED.current_goals, planning_time = EXCLUDED.planning_time
            WHERE profile.owner_id = EXCLUDED.owner_id
            """,
            (principal.subject, body.primary_focus, body.current_goals, body.planning_time),
        )
    return Onboarding(status="completed", **body.model_dump())


@router.post("/skip")
def skip_onboarding(principal: Principal, response: Response) -> Onboarding:
    response.headers["Cache-Control"] = "no-store"
    with onboarding_connection(principal.subject) as connection:
        connection.execute(
            """
            INSERT INTO public.momentum_onboarding (owner_id, status)
            VALUES (%s, 'skipped') ON CONFLICT (owner_id) DO NOTHING
            """,
            (principal.subject,),
        )
        result = read_onboarding(connection, principal.subject)
        if result is None:
            raise DatabaseError("The onboarding record could not be read.")
        return result
