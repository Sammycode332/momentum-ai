from collections.abc import Iterator
from contextlib import contextmanager
import logging
from os import environ
from pathlib import Path
import re

import psycopg
from dotenv import dotenv_values
from psycopg.conninfo import conninfo_to_dict

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
logger = logging.getLogger(__name__)

_SQLSTATE_MESSAGES = {
    "28P01": "Database password authentication failed.",
    "28000": "Database authorization failed.",
    "42501": "Database permission denied.",
    "42P01": "Required database relation is missing.",
    "42703": "Required database column is missing.",
    "3D000": "Configured database does not exist.",
    "53300": "Database connection limit reached.",
    "57P03": "Database is temporarily unavailable.",
    "57014": "Database operation was cancelled or timed out.",
    "23503": "Database foreign key constraint rejected the operation.",
    "23505": "Database uniqueness constraint rejected the operation.",
    "23514": "Database check constraint rejected the operation.",
    "XX000": "Database reported an internal server error.",
}


class DatabaseConfigurationError(ValueError):
    pass


class DatabaseError(RuntimeError):
    pass


def _log_database_failure(error: Exception, phase: str) -> None:
    state = getattr(error, "sqlstate", None)
    state = state if isinstance(state, str) and re.fullmatch(r"[0-9A-Z]{5}", state) else "unavailable"
    message = _SQLSTATE_MESSAGES.get(state, "Database operation failed.")
    if isinstance(error, DatabaseConfigurationError):
        message = "Database URL configuration is missing or invalid."
    elif isinstance(error, DatabaseError):
        message = "Application database safety check failed."
    elif state == "unavailable" and isinstance(error, psycopg.OperationalError):
        # Inspect locally to classify libpq failures, but emit only fixed text.
        diagnostic = str(error).casefold()
        for marker, summary in (
            ("password authentication failed", "Database password authentication failed."),
            ("failed to resolve host", "Database hostname resolution failed."),
            ("could not translate host name", "Database hostname resolution failed."),
            ("channel binding", "Database channel binding negotiation failed."),
            ("ssl", "Database TLS negotiation failed."),
            ("timeout", "Database connection timed out."),
            ("connection refused", "Database connection was refused."),
        ):
            if marker in diagnostic:
                message = summary
                break
    logger.warning(
        "Database failure phase=%s type=%s sqlstate=%s message=%s",
        phase, type(error).__name__, state, message,
    )


def _database_url() -> str:
    url = environ.get("DATABASE_URL")
    if url is None:
        url = dotenv_values(_ENV_FILE, interpolate=False).get("DATABASE_URL")
    if not url or not url.strip():
        raise DatabaseConfigurationError(
            "Set DATABASE_URL in the backend environment or backend/.env."
        )

    message = "DATABASE_URL must be a PostgreSQL URI with a host, database, user, and password."
    if not url.startswith(("postgresql://", "postgres://")):
        raise DatabaseConfigurationError(message)
    try:
        parameters = conninfo_to_dict(url)
    except psycopg.Error:
        raise DatabaseConfigurationError(message) from None

    host = parameters.get("host", "")
    if (
        not host
        or any(character in host for character in ("/", "\\", ",", "@"))
        or not all(parameters.get(key) for key in ("dbname", "user", "password"))
    ):
        raise DatabaseConfigurationError(message)
    return url


@contextmanager
def database_connection() -> Iterator[psycopg.Connection]:
    """Open one transaction for a synchronous backend operation and close it on exit."""
    try:
        url = _database_url()
    except DatabaseConfigurationError as error:
        _log_database_failure(error, "configuration")
        raise
    phase = "connect"
    try:
        with psycopg.connect(
            url,
            sslmode="require",
            channel_binding="require",
            gssencmode="disable",
            connect_timeout=5,
        ) as connection:
            phase = "transaction"
            yield connection
    except psycopg.Error as error:
        _log_database_failure(error, phase)
        raise DatabaseError("The database operation failed.") from None
    except DatabaseError as error:
        _log_database_failure(error, phase)
        raise


def main() -> int:
    try:
        with database_connection() as connection:
            result = connection.execute("SELECT 1").fetchone()
    except DatabaseConfigurationError as error:
        print(error)
        return 2
    except DatabaseError:
        print("Database connectivity check failed. Check the Neon branch, credentials, and network.")
        return 1

    if result != (1,):
        print("Database connectivity check returned an unexpected result.")
        return 1
    print("Database connectivity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
