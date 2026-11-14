from contextlib import contextmanager
from datetime import datetime, UTC
from unittest.mock import Mock
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.main import app
from app import conversation, actions, memory
from app.api_errors import ApiError
from app.practice import Packet, validate_transition
from app.discovery import normalize_jobs
from app.push import validate_endpoint
from app.reminder_worker import quiet_until, next_daily


def test_disabled_personalization_does_not_retrieve_private_context(monkeypatch):
    monkeypatch.setattr(conversation,'personalization_enabled',lambda _:False)
    context=Mock(side_effect=AssertionError('Personalization is disabled'))
    monkeypatch.setattr(conversation,'load_planning_context',context)
    monkeypatch.setattr(conversation,'relevant_memories',context)
    provider=Mock();provider.generate.return_value='{"reply":"A direct answer."}'
    monkeypatch.setattr(conversation,'get_planning_provider',lambda:provider)
    conversation.generate_reply(conversation.ChatRequest(messages=[{'role':'user','content':'Explain tides'}]),'synthetic')
    assert provider.generate.call_args.args[0]['workspace']=={}
    context.assert_not_called()


def test_low_score_cannot_advance_tutoring():
    packet=Packet(explanation='Example',question='Try again',rubric=['Accuracy'],feedback='Review this',score=2,revision='Practice',topic_index=1)
    with pytest.raises(ApiError):validate_transition(packet,0,3)
    validate_transition(packet.model_copy(update={'score':3}),0,3)
    with pytest.raises(ApiError):validate_transition(packet.model_copy(update={'topic_index':2,'score':5}),0,3)


def test_quiet_hours_wrap_midnight_and_recurrence_keeps_local_time():
    now=datetime(2026,11,13,23,0,tzinfo=UTC)
    assert quiet_until(now,'Africa/Lagos',1320,420)==datetime(2026,11,14,6,0,tzinfo=UTC)
    assert quiet_until(now,'UTC',0,0) is None
    # US fall-back: 09:00 remains 09:00 local as UTC offset changes.
    due=datetime(2026,10,31,13,0,tzinfo=UTC)
    assert next_daily(due,due,'America/New_York')==datetime(2026,11,1,14,0,tzinfo=UTC)


@pytest.mark.parametrize('url',['http://fcm.googleapis.com/x','https://localhost/x','https://fcm.googleapis.com.evil.test/x','https://fcm.googleapis.com@127.0.0.1/x','https://fcm.googleapis.com:8443/x'])
def test_push_rejects_untrusted_destinations(url):
    with pytest.raises(ValueError):validate_endpoint(url)


def test_source_filters_untrusted_urls_and_duplicates():
    job={'id':1,'title':'Designer','url':'https://remotive.com/remote-jobs/design/example'}
    result=normalize_jobs([job,job,{**job,'url':'javascript:alert(1)'},{**job,'url':'https://evil.test/job'}])
    assert len(result)==1 and result[0]['deadline'] is None


def test_applied_action_retry_does_not_execute_again(monkeypatch):
    row={'id':uuid4(),'status':'applied','result_id':uuid4()}
    cursor=Mock();cursor.execute.return_value.fetchone.return_value=row
    @contextmanager
    def private(*args):yield cursor
    monkeypatch.setattr(actions,'private_cursor',private)
    execute=Mock(side_effect=AssertionError('Duplicate action'))
    monkeypatch.setattr(actions,'execute',execute)
    from app.auth import AuthenticatedPrincipal
    assert actions.approve(row['id'],AuthenticatedPrincipal(subject='synthetic'))==row
    execute.assert_not_called()


def test_memory_rejects_owner_injection_and_unbounded_content():
    with pytest.raises(ValidationError):memory.MemoryInput(content='Preference',owner_id='another')
    with pytest.raises(ValidationError):memory.MemoryInput(content='x'*501)


def test_new_private_routes_require_authentication_and_large_body_is_rejected():
    with TestClient(app) as client:
        for path in ('memory','practice','reminders','actions','push/configuration'):
            assert client.get('/api/v1/'+path).status_code==401
        response=client.post('/api/v1/ai/chat',content=b'x'*65537)
        assert response.status_code==413
