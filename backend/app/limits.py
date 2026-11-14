"""Shared per-user AI request budgets and bounded HTTP request bodies."""
from datetime import datetime, UTC, timedelta
from fastapi import Request
from starlette.responses import JSONResponse
from app.private_store import Principal, private_cursor
from app.api_errors import ApiError

AI_PATHS = {'/api/v1/ai/chat', '/api/v1/ai/plan', '/api/v1/ai/conversations/{chat_id}/turns',
            '/api/v1/practice', '/api/v1/practice/{session_id}/answers', '/api/v1/actions/suggest'}


def reserve_budget(owner, now=None):
    now = now or datetime.now(UTC)
    windows = [('hour', now.replace(minute=0, second=0, microsecond=0), 20),
               ('day', now.replace(hour=0, minute=0, second=0, microsecond=0), 100)]
    with private_cursor(owner, 'momentum_ai_usage') as c:
        c.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,1))', (owner,))
        c.execute('DELETE FROM momentum_ai_usage WHERE owner_id=%s AND window_start<%s', (owner, now-timedelta(days=2)))
        for period, start, limit in windows:
            row = c.execute('''INSERT INTO momentum_ai_usage(owner_id,window_start,period,count)
                VALUES (%s,%s,%s,1) ON CONFLICT(owner_id,window_start,period)
                DO UPDATE SET count=momentum_ai_usage.count+1 WHERE momentum_ai_usage.count<%s RETURNING count''',
                (owner,start,period,limit)).fetchone()
            if row is None:
                raise ApiError(429,'AI_BUDGET_REACHED','Your AI request limit has been reached. Try again after the next hour or day.')


def require_ai_budget(request: Request, principal: Principal):
    if request.method == 'POST' and request.scope['route'].path in AI_PATHS:
        reserve_budget(principal.subject)


class BodyLimitMiddleware:
    def __init__(self, app, maximum=65536):
        self.app, self.maximum = app, maximum

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            size += len(message.get('body', b''))
            if size > self.maximum:
                response = JSONResponse({'error': {'code': 'REQUEST_TOO_LARGE', 'message': 'The request is too large.'}}, status_code=413)
                return await response(scope, receive, send)
            chunks.append(message)
            if not message.get('more_body', False):
                break
        async def bounded_receive():
            if chunks:
                return chunks.pop(0)
            return await receive()
        await self.app(scope, bounded_receive, send)
