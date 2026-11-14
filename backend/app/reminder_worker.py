"""Run once per minute in a supervised scheduler; no browser is required."""
from datetime import datetime, UTC, timedelta
from os import getenv
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo
from dotenv import dotenv_values
import psycopg
from psycopg.rows import dict_row


def quiet_until(now,zone,start,end):
    local=now.astimezone(ZoneInfo(zone)); minute=local.hour*60+local.minute
    quiet=(start<=minute<end) if start<end else (minute>=start or minute<end) if start>end else False
    if not quiet: return None
    day=local.date()+timedelta(days=1 if start>end and minute>=start else 0)
    return datetime(day.year,day.month,day.day,end//60,end%60,tzinfo=ZoneInfo(zone)).astimezone(UTC)


def next_daily(due,now,zone):
    z=ZoneInfo(zone); previous=due.astimezone(z); today=now.astimezone(z)
    candidate=today.replace(hour=previous.hour,minute=previous.minute,second=0,microsecond=0)
    if candidate.astimezone(UTC)<=now: candidate+=timedelta(days=1)
    return candidate.astimezone(UTC)


def dispatch(connection,now):
    delivered=0
    with connection.cursor(row_factory=dict_row) as c:
        rows=c.execute("""SELECT r.*,COALESCE(p.notifications_enabled,true) AS enabled,
            COALESCE(p.timezone,r.timezone) AS preference_zone,COALESCE(p.quiet_start,1320) AS quiet_start,
            COALESCE(p.quiet_end,420) AS quiet_end FROM momentum_reminders r
            LEFT JOIN momentum_preferences p ON p.owner_id=r.owner_id
            WHERE r.status='scheduled' AND r.due_at<=%s AND r.next_check<=%s ORDER BY r.due_at LIMIT 100 FOR UPDATE OF r SKIP LOCKED""",(now,now)).fetchall()
        for row in rows:
            if not row['enabled']:
                c.execute("UPDATE momentum_reminders SET next_check=%s WHERE id=%s AND owner_id=%s",(now+timedelta(minutes=15),row['id'],row['owner_id']))
                continue
            quiet=quiet_until(now,row['preference_zone'],row['quiet_start'],row['quiet_end'])
            if quiet:
                c.execute("UPDATE momentum_reminders SET next_check=%s WHERE id=%s AND owner_id=%s",(quiet,row['id'],row['owner_id']))
                continue
            c.execute('INSERT INTO momentum_notifications(id,owner_id,reminder_id,occurrence,title) VALUES (%s,%s,%s,%s,%s) ON CONFLICT(reminder_id,occurrence) DO NOTHING',
                      (uuid4(),row['owner_id'],row['id'],row['occurrence'],row['title']))
            delivered+=c.rowcount
            if row['repeat']=='daily':
                c.execute('UPDATE momentum_reminders SET due_at=%s,occurrence=occurrence+1 WHERE id=%s AND owner_id=%s',
                          (next_daily(row['due_at'],now,row['timezone']),row['id'],row['owner_id']))
            else:
                c.execute("UPDATE momentum_reminders SET status='delivered' WHERE id=%s AND owner_id=%s",(row['id'],row['owner_id']))
    return delivered


def main():
    local=dotenv_values(Path(__file__).resolve().parents[1]/'.env',interpolate=False)
    url=getenv('REMINDER_DATABASE_URL') or local.get('REMINDER_DATABASE_URL')
    if not url:
        print('Worker not configured. Set REMINDER_DATABASE_URL for the restricted scheduler role.');return 2
    try:
        with psycopg.connect(url,sslmode='require',channel_binding='require',connect_timeout=5) as connection:
            if connection.execute("SELECT pg_has_role(current_user,'momentum_scheduler','member'),rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user").fetchone() != (True,False,False):
                print('Worker requires a nonprivileged scheduler member.');return 2
            count=dispatch(connection,datetime.now(UTC))
            connection.commit()
            from app.push_worker import dispatch_push
            push=dispatch_push(connection,datetime.now(UTC))
        print(f"Push dispatch: sent={push['sent']} failed={push['failed']} configured={push['configured']}")
        print(f'Reminder dispatch completed: {count} notifications.');return 0
    except (psycopg.Error,ValueError):
        print('Reminder dispatch failed. Check worker configuration and schema; no private data logged.');return 1


if __name__=='__main__': raise SystemExit(main())
