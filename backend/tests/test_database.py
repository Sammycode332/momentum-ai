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
