from contextlib import contextmanager
from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from psycopg.rows import dict_row
from psycopg.errors import LockNotAvailable

from app.auth import AuthenticatedPrincipal, require_authenticated_principal
from app.database import database_connection, DatabaseError, DatabaseConfigurationError
from app.api_errors import ApiError

Principal = Annotated[AuthenticatedPrincipal, Depends(require_authenticated_principal)]


@contextmanager
def private_cursor(owner: str, *tables: str):
    try:
        with database_connection() as connection:
            for table in tables:
                if connection.execute('SELECT row_security_active(%s::regclass)', (f'public.{table}',)).fetchone() != (True,):
                    raise DatabaseError('RLS required')
            connection.execute("SELECT set_config('momentum.user_id', %s, true)", (owner,))
            with connection.cursor(row_factory=dict_row) as cursor:
                try:
                    yield cursor
                except LockNotAvailable:
                    raise ApiError(409, 'RESOURCE_BUSY', 'This item is being updated. Try again shortly.') from None
    except (DatabaseError, DatabaseConfigurationError):
        raise ApiError(503, 'STORAGE_UNAVAILABLE', 'Storage is unavailable. Check service setup and try again.') from None


def audit(cursor, owner, event, target):
    cursor.execute('INSERT INTO momentum_audit (id,owner_id,event,target_id) VALUES (%s,%s,%s,%s)',
                   (uuid4(), owner, event, target))


def require_row(row):
    if row is None:
        raise ApiError(404, 'NOT_FOUND', 'Item not found.')
    return row
