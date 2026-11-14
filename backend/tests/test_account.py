from contextlib import contextmanager
import os
from unittest.mock import Mock
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from app import account
from app.api_errors import ApiError
from app.auth import AuthenticatedPrincipal, get_token_verifier
from app.main import app
from app import private_store


def test_export_is_bounded_and_uses_verified_owner(monkeypatch):
    cursor = Mock()
    cursor.execute.return_value.fetchall.return_value = [{'id': str(n)} for n in range(201)]
    owners = []
    @contextmanager
    def private(owner, table):
        owners.append((owner, table))
        yield cursor
    monkeypatch.setattr(account, 'private_cursor', private)
    result = account.export_page('goals', AuthenticatedPrincipal(subject='synthetic-a'), 200)
    assert owners == [('synthetic-a', 'momentum_goals')]
    sql, params = cursor.execute.call_args.args
    assert 'WHERE owner_id=%s' in sql
    assert params == ('synthetic-a', 201, 200)
    assert len(result['items']) == 200 and result['next_offset'] == 400
    cursor.execute.return_value.fetchall.return_value = []
    assert account.export_page('goals', AuthenticatedPrincipal(subject='synthetic-b'), 0)['next_offset'] is None
    assert owners[-1][0] == 'synthetic-b'


def test_unknown_export_section_never_reaches_storage(monkeypatch):
    store = Mock(side_effect=AssertionError('Unexpected database access'))
    monkeypatch.setattr(account, 'private_cursor', store)
    with pytest.raises(ApiError) as error:
        account.export_page('momentum_push_subscriptions', AuthenticatedPrincipal(subject='synthetic'), 0)
    assert error.value.status_code == 404
    store.assert_not_called()
    for table, columns, _ in account.SECTIONS.values():
        assert 'push' not in table
        assert not {'endpoint', 'auth', 'p256dh', 'password', 'token'}.intersection(columns.split(','))


def test_export_auth_and_offset_validation(monkeypatch, token_verifier, access_token):
    monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)
    with TestClient(app) as client:
        assert client.get('/api/v1/account/export').status_code == 401
        headers = {'Authorization': f'Bearer {access_token()}'}
        assert client.get('/api/v1/account/export', headers=headers).status_code == 200
        assert client.get('/api/v1/account/export/goals?offset=-1', headers=headers).status_code == 422
        assert client.get('/api/v1/account/export/goals?offset=100001', headers=headers).status_code == 422
        assert client.get('/health/live').json() == {'status': 'ok'}


def test_export_separates_tenants_on_postgres(monkeypatch, token_verifier, access_token):
    url = os.getenv('GOALS_TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set GOALS_TEST_DATABASE_URL to an isolated restricted-role database with migrations 001–014.')

    owners = [str(uuid4()), str(uuid4())]
    try:
        with psycopg.connect(url, sslmode='require', channel_binding='require', connect_timeout=5) as connection:
            role = connection.execute('SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user').fetchone()
            assert role == (False, False)

            @contextmanager
            def database_connection():
                with connection.transaction():
                    yield connection

            monkeypatch.setattr(private_store, 'database_connection', database_connection)
            monkeypatch.setitem(app.dependency_overrides, get_token_verifier, lambda: token_verifier)

            try:
                for index, owner in enumerate(owners):
                    connection.execute("SELECT set_config('momentum.user_id', %s, true)", (owner,))
                    connection.execute('INSERT INTO momentum_goals (id, owner_id, title) VALUES (%s, %s, %s)',
                                       (uuid4(), owner, f'Synthetic goal {index}'))
                    connection.execute('INSERT INTO momentum_memories (id, owner_id, content) VALUES (%s, %s, %s)',
                                       (uuid4(), owner, f'Synthetic memory {index}'))

                fields = {'goals': ('title', 'goal'), 'memories': ('content', 'memory')}
                with TestClient(app) as client:
                    for index, owner in enumerate(owners):
                        headers = {'Authorization': f'Bearer {access_token(subject=owner)}'}
                        for section, (field, label) in fields.items():
                            response = client.get(f'/api/v1/account/export/{section}', headers=headers)
                            assert response.status_code == 200
                            page = response.json()
                            assert [record[field] for record in page['items']] == [f'Synthetic {label} {index}']
                            assert page['next_offset'] is None
            finally:
                connection.rollback()
    except psycopg.Error:
        pytest.fail('Restricted PostgreSQL export check could not complete. Check connectivity and schema.', pytrace=False)
