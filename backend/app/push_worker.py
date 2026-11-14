"""Durable push retries. Called by the reminder worker after its dispatch commit."""
from datetime import timedelta
from psycopg.rows import dict_row
from app.push import configuration, send


def dispatch_push(connection,now):
    if not all(configuration().values()): return {'sent':0,'failed':0,'configured':False}
    from app.reminder_worker import quiet_until
    sent=failed=0
    with connection.cursor(row_factory=dict_row) as c:
        c.execute('''INSERT INTO momentum_push_deliveries(notification_id,subscription_id,owner_id)
            SELECT n.id,s.id,n.owner_id FROM momentum_notifications n
            JOIN momentum_push_subscriptions s ON s.owner_id=n.owner_id AND s.created_at<=n.created_at
            WHERE n.created_at>%s AND n.state='unread' ON CONFLICT DO NOTHING''',(now-timedelta(days=1),))
        rows=c.execute('''SELECT d.*,s.endpoint,s.p256dh,s.auth,n.state,n.created_at,
            COALESCE(p.notifications_enabled,true) AS enabled,COALESCE(p.timezone,'UTC') AS timezone,
            COALESCE(p.quiet_start,1320) AS quiet_start,COALESCE(p.quiet_end,420) AS quiet_end
            FROM momentum_push_deliveries d JOIN momentum_push_subscriptions s ON s.id=d.subscription_id AND s.owner_id=d.owner_id
            JOIN momentum_notifications n ON n.id=d.notification_id AND n.owner_id=d.owner_id
            LEFT JOIN momentum_preferences p ON p.owner_id=d.owner_id
            WHERE d.status='pending' AND d.next_attempt<=%s ORDER BY d.next_attempt LIMIT 20 FOR UPDATE OF d SKIP LOCKED''',(now,)).fetchall()
        for row in rows:
            key=(row['notification_id'],row['subscription_id'],row['owner_id'])
            if row['state']!='unread' or row['created_at']<now-timedelta(days=1):
                c.execute("UPDATE momentum_push_deliveries SET status='failed' WHERE notification_id=%s AND subscription_id=%s AND owner_id=%s",key)
                continue
            quiet=quiet_until(now,row['timezone'],row['quiet_start'],row['quiet_end'])
            if not row['enabled'] or quiet:
                c.execute('UPDATE momentum_push_deliveries SET next_attempt=%s WHERE notification_id=%s AND subscription_id=%s AND owner_id=%s',((quiet or now+timedelta(minutes=15)),*key))
                continue
            try: status=send(row,row['notification_id'])
            except (ValueError,ImportError): status=503
            if status in (404,410):
                c.execute('DELETE FROM momentum_push_subscriptions WHERE id=%s AND owner_id=%s',(row['subscription_id'],row['owner_id']))
                failed+=1;continue
            attempts=row['attempts']+1
            result='sent' if 200<=status<300 else 'failed' if attempts>=5 or (300<=status<500 and status not in (408,429)) else 'pending'
            c.execute('''UPDATE momentum_push_deliveries SET status=%s,attempts=%s,next_attempt=%s
                WHERE notification_id=%s AND subscription_id=%s AND owner_id=%s''',
                (result,attempts,now+timedelta(minutes=2**attempts),*key))
            sent+=result=='sent';failed+=result=='failed'
    return {'sent':sent,'failed':failed,'configured':True}
