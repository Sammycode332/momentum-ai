from collections.abc import Iterator
from contextlib import contextmanager
from os import environ
from pathlib import Path

import psycopg
from dotenv import dotenv_values
from psycopg.conninfo import conninfo_to_dict

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class DatabaseConfigurationError(ValueError):
    pass


class DatabaseError(RuntimeError):
    pass


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
    url = _database_url()
    try:
        with psycopg.connect(
            url,
            sslmode="require",
            channel_binding="require",
            gssencmode="disable",
            connect_timeout=5,
        ) as connection:
            yield connection
    except psycopg.Error:
        raise DatabaseError("The database operation failed.") from None


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
