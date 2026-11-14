from contextlib import contextmanager
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from app import account
from app.api_errors import ApiError
from app.auth import AuthenticatedPrincipal, get_token_verifier
from app.main import app


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
