from unittest.mock import MagicMock

import psycopg
import pytest

from app import database

TEST_URL = "postgresql://test_user:test_password@db.example.test/test_db"


@pytest.fixture(autouse=True)
def isolated_database(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(database, "_ENV_FILE", tmp_path / ".env")
    connect = MagicMock(side_effect=AssertionError("Unexpected database connection"))
    monkeypatch.setattr(database.psycopg, "connect", connect)
    return connect


@pytest.mark.parametrize("url", [None, "", "https://example.test", "postgresql://?bad=value"])
def test_check_rejects_missing_or_invalid_configuration(
    url, monkeypatch, isolated_database, capsys
):
    if url is not None:
        monkeypatch.setenv("DATABASE_URL", url)

    assert database.main() == 2
    assert "DATABASE_URL" in capsys.readouterr().out
    isolated_database.assert_not_called()


def test_check_uses_local_backend_env_when_process_value_is_absent(
    isolated_database, capsys
):
    database._ENV_FILE.write_text(f"DATABASE_URL={TEST_URL}\n", encoding="utf-8")
    isolated_database.side_effect = None
    context = isolated_database.return_value
    connection = context.__enter__.return_value
    connection.execute.return_value.fetchone.return_value = (1,)

    assert database.main() == 0
    isolated_database.assert_called_once_with(
        TEST_URL,
        sslmode="require",
        channel_binding="require",
        gssencmode="disable",
        connect_timeout=5,
    )
    connection.execute.assert_called_once_with("SELECT 1")
    context.__exit__.assert_called_once_with(None, None, None)
    assert capsys.readouterr().out == "Database connectivity check passed.\n"


def test_process_environment_takes_precedence_and_security_options_are_enforced(
    monkeypatch, isolated_database
):
    database._ENV_FILE.write_text("DATABASE_URL=invalid\n", encoding="utf-8")
    url = f"{TEST_URL}?sslmode=disable&channel_binding=disable"
    monkeypatch.setenv("DATABASE_URL", url)
    isolated_database.side_effect = None

    with database.database_connection():
        pass

    assert isolated_database.call_args.args == (url,)
    assert isolated_database.call_args.kwargs["sslmode"] == "require"
    assert isolated_database.call_args.kwargs["channel_binding"] == "require"


def test_check_reports_connection_failure_without_driver_details(
    monkeypatch, isolated_database, capsys
):
    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    isolated_database.side_effect = psycopg.OperationalError(TEST_URL)

    assert database.main() == 1
    captured = capsys.readouterr()
    assert "Database connectivity check failed." in captured.out
    assert TEST_URL not in captured.out + captured.err


@pytest.mark.parametrize("error, message, state", [
    (psycopg.errors.InvalidPassword('password authentication failed for user "private-user"'),
     "Database password authentication failed.", "28P01"),
    (psycopg.errors.InsufficientPrivilege('permission denied for table "private-table"'),
     "Database permission denied.", "42501"),
    (psycopg.errors.UndefinedTable('relation "private-table" does not exist'),
     "Required database relation is missing.", "42P01"),
    (psycopg.errors.UndefinedColumn('column "private-column" does not exist'),
     "Required database column is missing.", "42703"),
    (psycopg.errors.CheckViolation('private-row-value'),
     "Database check constraint rejected the operation.", "23514"),
    (psycopg.OperationalError(f'failed to resolve host: {TEST_URL}'),
     "Database hostname resolution failed.", "unavailable"),
    (psycopg.OperationalError(f'channel binding failed: {TEST_URL}'),
     "Database channel binding negotiation failed.", "unavailable"),
    (psycopg.OperationalError(f'SSL error: {TEST_URL}'),
     "Database TLS negotiation failed.", "unavailable"),
    (psycopg.OperationalError(f'connection timeout: {TEST_URL}'),
     "Database connection timed out.", "unavailable"),
    (psycopg.OperationalError(f'Unexpected private-row-value {TEST_URL}'),
     "Database operation failed.", "unavailable"),
])
def test_connection_diagnostics_keep_only_safe_summary(
    error, message, state, monkeypatch, isolated_database, caplog
):
    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    isolated_database.side_effect = error

    with pytest.raises(database.DatabaseError, match="^The database operation failed\\.$"):
        with database.database_connection():
            pytest.fail("Connection should fail before yielding")

    assert f"phase=connect type={type(error).__name__} sqlstate={state}" in caplog.text
    assert message in caplog.text
    assert str(error) not in caplog.text
    assert TEST_URL not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)


@pytest.mark.parametrize("phase", ["query", "commit", "guard"])
def test_transaction_failure_is_logged_without_changing_rollback_or_errors(
    phase, monkeypatch, isolated_database, caplog
):
    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    isolated_database.side_effect = None
    context = isolated_database.return_value
    error = psycopg.errors.InsufficientPrivilege("private-record-value")
    if phase == "commit":
        context.__exit__.side_effect = error

    with pytest.raises(database.DatabaseError) as failure:
        with database.database_connection():
            if phase == "query":
                raise error
            if phase == "guard":
                raise database.DatabaseError("private-guard-value")

    assert "phase=transaction" in caplog.text
    assert "private-record-value" not in caplog.text
    assert "private-guard-value" not in caplog.text
    if phase == "guard":
        assert "Application database safety check failed." in caplog.text
        assert str(failure.value) == "private-guard-value"
    else:
        assert "sqlstate=42501" in caplog.text
        assert str(failure.value) == "The database operation failed."
    if phase == "query":
        assert context.__exit__.call_args.args[1] is error


def test_invalid_configuration_is_logged_without_attempting_connection(
    monkeypatch, isolated_database, caplog
):
    monkeypatch.setenv("DATABASE_URL", "https://private-user:private-password@example.test")
    with pytest.raises(database.DatabaseConfigurationError):
        with database.database_connection():
            pytest.fail("Invalid configuration should fail before yielding")
    assert "phase=configuration type=DatabaseConfigurationError sqlstate=unavailable" in caplog.text
    assert "Database URL configuration is missing or invalid." in caplog.text
    assert "private-user" not in caplog.text
    assert "private-password" not in caplog.text
    isolated_database.assert_not_called()
