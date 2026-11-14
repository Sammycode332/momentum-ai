from datetime import datetime, UTC, timedelta
from typing import Annotated, Literal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, AwareDatetime, StrictBool, field_validator
from app.private_store import Principal, private_cursor, require_row
from app.api_errors import ApiError

router=APIRouter(prefix='/api/v1/reminders',tags=['reminders'])
TABLES=('momentum_reminders','momentum_notifications','momentum_preferences')
FIELDS='id,title,due_at,timezone,repeat,status,occurrence'
Title=Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=200,pattern=r'^[^\x00]+$')]


def valid_zone(value):
    try: ZoneInfo(value)
    except (ZoneInfoNotFoundError,ValueError): raise ValueError('Choose an IANA timezone.') from None
    return value


class ReminderInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title: Title
    due_at: AwareDatetime
    timezone: str='UTC'
    repeat: Literal['none','daily']='none'
    _zone=field_validator('timezone')(valid_zone)

    @field_validator('due_at')
    @classmethod
    def future(cls,value):
        if value <= datetime.now(UTC) or value > datetime.now(UTC)+timedelta(days=3650):
            raise ValueError('Choose a future date within ten years.')
        return value


class ReminderCreate(ReminderInput):
    id: UUID


class NotificationPreferences(BaseModel):
    model_config=ConfigDict(extra='forbid')
    timezone: str
    notifications_enabled: StrictBool
    quiet_start: Annotated[int,Field(ge=0,le=1439,strict=True)]
    quiet_end: Annotated[int,Field(ge=0,le=1439,strict=True)]
    _zone=field_validator('timezone')(valid_zone)


class NotificationState(BaseModel):
    model_config=ConfigDict(extra='forbid')
    state: Literal['read','dismissed']


class NotificationBatch(NotificationState):
    ids: Annotated[list[UUID], Field(min_length=1, max_length=100)]


@router.get('')
def reminders(principal: Principal):
    with private_cursor(principal.subject,*TABLES) as c:
        return c.execute(f"SELECT {FIELDS} FROM momentum_reminders WHERE owner_id=%s ORDER BY CASE WHEN status='scheduled' THEN 0 ELSE 1 END,due_at,id LIMIT 100",(principal.subject,)).fetchall()


@router.post('',status_code=201)
def create(body: ReminderCreate,principal: Principal):
    with private_cursor(principal.subject,*TABLES) as c:
        c.execute('INSERT INTO momentum_reminders(id,owner_id,title,due_at,timezone,repeat) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING',
                  (body.id,principal.subject,body.title,body.due_at,body.timezone,body.repeat))
        row=require_row(c.execute(f'SELECT {FIELDS} FROM momentum_reminders WHERE id=%s AND owner_id=%s',(body.id,principal.subject)).fetchone())
        if any(row[k]!=getattr(body,k) for k in ('title','due_at','timezone','repeat')):
            raise ApiError(409,'REQUEST_CONFLICT','This reminder ID was already used.')
        return row


@router.get('/preferences')
def preferences(principal: Principal):
    with private_cursor(principal.subject,*TABLES) as c:
        return c.execute('SELECT timezone,notifications_enabled,quiet_start,quiet_end FROM momentum_preferences WHERE owner_id=%s',(principal.subject,)).fetchone() or {
            'timezone':'UTC','notifications_enabled':True,'quiet_start':1320,'quiet_end':420}


@router.put('/preferences')
def save_preferences(body: NotificationPreferences,principal: Principal):
    with private_cursor(principal.subject,*TABLES) as c:
        c.execute('''INSERT INTO momentum_preferences(owner_id,timezone,notifications_enabled,quiet_start,quiet_end)
            VALUES (%s,%s,%s,%s,%s) ON CONFLICT(owner_id) DO UPDATE SET timezone=EXCLUDED.timezone,
            notifications_enabled=EXCLUDED.notifications_enabled,quiet_start=EXCLUDED.quiet_start,quiet_end=EXCLUDED.quiet_end''',
            (principal.subject,body.timezone,body.notifications_enabled,body.quiet_start,body.quiet_end))
        c.execute("UPDATE momentum_reminders SET next_check=now() WHERE owner_id=%s AND status='scheduled'",(principal.subject,))
    return body


@router.get('/notifications')
def notifications(principal: Principal):
    with private_cursor(principal.subject,*TABLES) as c:
        return c.execute('SELECT id,title,created_at,state,snoozed FROM momentum_notifications WHERE owner_id=%s ORDER BY created_at DESC,id LIMIT 100',(principal.subject,)).fetchall()


@router.post('/test',status_code=201)
def test_notification(principal: Principal):
    with private_cursor(principal.subject,*TABLES) as c:
        reminder_id=uuid4()
        c.execute("INSERT INTO momentum_reminders(id,owner_id,title,due_at,timezone,repeat,status) VALUES (%s,%s,'Test notification',now(),'UTC','none','delivered')",(reminder_id,principal.subject))
        return c.execute("INSERT INTO momentum_notifications(id,owner_id,reminder_id,occurrence,title) VALUES (%s,%s,%s,0,'Your in-app notifications are working.') RETURNING id",(uuid4(),principal.subject,reminder_id)).fetchone()


@router.patch('/notifications')
def mark_batch(body: NotificationBatch, principal: Principal):
    with private_cursor(principal.subject, *TABLES) as c:
        c.execute('''UPDATE momentum_notifications SET state=%s
            WHERE owner_id=%s AND id=ANY(%s) AND state<>'dismissed'
            AND (%s='dismissed' OR state='unread')''',
            (body.state, principal.subject, list(set(body.ids)), body.state))
        return {'updated': c.rowcount}


@router.patch('/notifications/{notification_id}')
def mark(notification_id: UUID,body: NotificationState,principal: Principal):
    with private_cursor(principal.subject,*TABLES) as c:
        return require_row(c.execute('UPDATE momentum_notifications SET state=%s WHERE id=%s AND owner_id=%s RETURNING id,state',(body.state,notification_id,principal.subject)).fetchone())


@router.post('/notifications/{notification_id}/snooze')
def snooze(notification_id: UUID,principal: Principal):
    with private_cursor(principal.subject,*TABLES) as c:
        row=require_row(c.execute('SELECT title,snoozed FROM momentum_notifications WHERE id=%s AND owner_id=%s FOR UPDATE',(notification_id,principal.subject)).fetchone())
        if not row['snoozed']:
            c.execute("INSERT INTO momentum_reminders(id,owner_id,title,due_at,timezone,repeat) VALUES (%s,%s,%s,now()+interval '30 minutes','UTC','none')",(uuid4(),principal.subject,row['title']))
            c.execute("UPDATE momentum_notifications SET snoozed=true,state='dismissed' WHERE id=%s AND owner_id=%s",(notification_id,principal.subject))
    return {'snoozed':True}


@router.put('/{reminder_id}')
def reschedule(reminder_id: UUID,body: ReminderInput,principal: Principal):
    with private_cursor(principal.subject,*TABLES) as c:
        return require_row(c.execute(f"UPDATE momentum_reminders SET title=%s,due_at=%s,timezone=%s,repeat=%s,status='scheduled',next_check=now(),occurrence=occurrence+1 WHERE id=%s AND owner_id=%s RETURNING {FIELDS}",
            (body.title,body.due_at,body.timezone,body.repeat,reminder_id,principal.subject)).fetchone())


@router.post('/{reminder_id}/cancel')
def cancel(reminder_id: UUID,principal: Principal):
    with private_cursor(principal.subject,*TABLES) as c:
        return require_row(c.execute("UPDATE momentum_reminders SET status='cancelled' WHERE id=%s AND owner_id=%s RETURNING id,status",(reminder_id,principal.subject)).fetchone())
