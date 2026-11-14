"""Push subscriptions are private credentials; never log their contents."""
from base64 import urlsafe_b64decode, urlsafe_b64encode
from os import getenv
from urllib.parse import urlsplit
from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, field_validator
from dotenv import dotenv_values
from app.api_errors import ApiError
from app.private_store import Principal, private_cursor
from app.reminders import insert_test_notification

router = APIRouter(prefix='/api/v1/push', tags=['push notifications'])


def configuration():
    local = dotenv_values(Path(__file__).resolve().parents[1]/'.env', interpolate=False)
    return {name: getenv(name) or local.get(name) or '' for name in ('VAPID_PUBLIC_KEY','VAPID_PRIVATE_KEY','VAPID_SUBJECT')}


def validate_endpoint(value):
    url = urlsplit(value)
    host = url.hostname or ''
    allowed = host in ('fcm.googleapis.com','updates.push.services.mozilla.com','web.push.apple.com') or host.endswith('.notify.windows.com')
    if not allowed or url.scheme != 'https' or url.port not in (None,443) or url.username or url.password or url.fragment:
        raise ValueError('Unsupported browser push service.')
    return value


class Endpoint(BaseModel):
    model_config = ConfigDict(extra='forbid')
    endpoint: str = Field(min_length=1,max_length=2048)
    _endpoint = field_validator('endpoint')(validate_endpoint)


class Subscription(Endpoint):
    p256dh: str = Field(min_length=1,max_length=100)
    auth: str = Field(min_length=1,max_length=30)

    @field_validator('p256dh','auth')
    @classmethod
    def validate_key(cls,value,info):
        try: raw = urlsafe_b64decode(value + '=' * (-len(value)%4))
        except (ValueError,TypeError): raise ValueError('Invalid push key.') from None
        if (info.field_name == 'auth' and len(raw)!=16) or (info.field_name == 'p256dh' and (len(raw)!=65 or raw[0]!=4)):
            raise ValueError('Invalid push key.')
        return value


@router.get('/configuration')
def public_key(principal: Principal):
    config = configuration()
    enabled = all(config.values())
    return {'enabled':enabled,'public_key':config['VAPID_PUBLIC_KEY'] if enabled else None}


@router.post('/subscriptions',status_code=201)
def subscribe(body: Subscription,principal: Principal):
    if not all(configuration().values()):
        raise ApiError(503,'PUSH_NOT_CONFIGURED','Push delivery has not been configured by the operator.')
    with private_cursor(principal.subject,'momentum_push_subscriptions') as c:
        # Never transfer another account's endpoint; sign-out disables the browser subscription.
        c.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,2))',(principal.subject,))
        count=c.execute('SELECT count(*) AS count FROM momentum_push_subscriptions WHERE owner_id=%s AND endpoint<>%s',(principal.subject,body.endpoint)).fetchone()['count']
        if count>=10: raise ApiError(409,'DEVICE_LIMIT','Remove an existing notification device before adding another.')
        c.execute('''INSERT INTO momentum_push_subscriptions(id,owner_id,endpoint,p256dh,auth) VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT(endpoint) DO UPDATE SET p256dh=EXCLUDED.p256dh,auth=EXCLUDED.auth
            WHERE momentum_push_subscriptions.owner_id=EXCLUDED.owner_id''',
            (uuid4(),principal.subject,body.endpoint,body.p256dh,body.auth))
        if c.rowcount != 1:
            raise ApiError(409,'SUBSCRIPTION_CONFLICT','Disable and re-enable push in browser settings before registering this device.')
        expired = c.execute('''SELECT 1 FROM momentum_push_deliveries d
            JOIN momentum_push_subscriptions s ON s.id=d.subscription_id AND s.owner_id=d.owner_id
            WHERE s.owner_id=%s AND s.endpoint=%s AND d.status='failed' AND d.next_attempt='infinity' LIMIT 1''',
            (principal.subject,body.endpoint)).fetchone()
        if expired:
            raise ApiError(409,'SUBSCRIPTION_EXPIRED','Disable and re-enable push on this device to renew its subscription.')
    return {'subscribed':True}


@router.delete('/subscriptions',status_code=204)
def unsubscribe(body: Endpoint,principal: Principal):
    with private_cursor(principal.subject,'momentum_push_subscriptions') as c:
        c.execute('DELETE FROM momentum_push_subscriptions WHERE owner_id=%s AND endpoint=%s',(principal.subject,body.endpoint))


@router.post('/test',status_code=201)
def test_push(body: Endpoint, principal: Principal):
    if not all(configuration().values()):
        raise ApiError(503,'PUSH_NOT_CONFIGURED','Push delivery has not been configured by the operator.')
    owner = principal.subject
    title = 'Push test notification'
    with private_cursor(principal.subject,'momentum_push_subscriptions','momentum_reminders',
                        'momentum_notifications','momentum_push_deliveries') as c:
        c.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,3))', (owner,))
        subscription = c.execute('''SELECT endpoint,p256dh,auth FROM momentum_push_subscriptions s
            WHERE s.owner_id=%s AND s.endpoint=%s
            AND NOT EXISTS (SELECT 1 FROM momentum_push_deliveries d WHERE d.owner_id=s.owner_id
                AND d.subscription_id=s.id AND d.status='failed' AND d.next_attempt='infinity') LIMIT 1''',
            (owner, body.endpoint)).fetchone()
        if subscription is None:
            raise ApiError(409,'NO_PUSH_DEVICE','Enable push on this device before sending a test.')
        recent = c.execute("""SELECT 1 FROM momentum_notifications WHERE owner_id=%s AND title=%s
            AND created_at > now() - interval '15 seconds' LIMIT 1""", (owner, title)).fetchone()
        if recent:
            raise ApiError(429,'PUSH_TEST_RATE_LIMIT','Wait 15 seconds before sending another push test.')
        notice = insert_test_notification(c, owner, title)

    try:
        status = send(subscription, notice['id'])
    except (ValueError, ImportError):
        raise ApiError(503,'PUSH_TEST_UNAVAILABLE','Push could not send the test. Check the server push configuration.') from None
    if status in (404, 410):
        raise ApiError(409,'SUBSCRIPTION_EXPIRED','Disable and re-enable push on this device, then try again.')
    if not 200 <= status < 300:
        raise ApiError(502,'PUSH_TEST_FAILED',f'The push service did not accept the test (HTTP {status}).')
    return {'id': notice['id'], 'accepted': True}


def send(subscription, notification_id):
    # Optional worker extra. Reject redirects even from an allowlisted service.
    from py_vapid import VapidException
    from pywebpush import webpush, WebPushException
    import requests
    class NoRedirectSession(requests.Session):
        def request(self,*args,**kwargs):
            kwargs['allow_redirects']=False
            return super().request(*args,**kwargs)
    config=configuration()
    validate_endpoint(subscription['endpoint'])
    import json
    with NoRedirectSession() as session:
        try:
            result=webpush(subscription_info={'endpoint':subscription['endpoint'],'keys':{'p256dh':subscription['p256dh'],'auth':subscription['auth']}},
                data=json.dumps({'title':'Momentum AI','body':'You have a reminder. Open your workspace to view it.','tag':str(notification_id)}),
                headers={'Topic': urlsafe_b64encode(notification_id.bytes).decode().rstrip('=')},
                vapid_private_key=config['VAPID_PRIVATE_KEY'],vapid_claims={'sub':config['VAPID_SUBJECT']},
                timeout=10,ttl=3600,requests_session=session)
            return result.status_code
        except WebPushException as error:
            return error.response.status_code if error.response is not None else 503
        except (requests.RequestException, VapidException):
            return 503
