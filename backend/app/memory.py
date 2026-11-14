import re
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, Response
from pydantic import BaseModel, ConfigDict, StrictBool, StringConstraints

from app.private_store import Principal, private_cursor, require_row, audit

router = APIRouter(prefix='/api/v1/memory', tags=['personal memory'])
TABLES = ('momentum_memories', 'momentum_preferences', 'momentum_audit')
FIELDS = 'id,content,status,created_at,updated_at'


class MemoryInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: Annotated[str, StringConstraints(strip_whitespace=True,min_length=1,max_length=500,pattern=r'^[^\x00]+$')]


class Preferences(BaseModel):
    model_config = ConfigDict(extra='forbid')
    personalization: StrictBool


@router.get('')
def list_memory(principal: Principal):
    with private_cursor(principal.subject, *TABLES) as c:
        return c.execute(f'SELECT {FIELDS} FROM momentum_memories WHERE owner_id=%s ORDER BY updated_at DESC,id LIMIT 100', (principal.subject,)).fetchall()


@router.post('', status_code=201)
def propose(body: MemoryInput, principal: Principal):
    with private_cursor(principal.subject, *TABLES) as c:
        row = c.execute(f"INSERT INTO momentum_memories(id,owner_id,content) VALUES (%s,%s,%s) RETURNING {FIELDS}",
                        (uuid4(),principal.subject,body.content)).fetchone()
        audit(c,principal.subject,'memory.proposed',row['id'])
        return row


@router.get('/preferences')
def preferences(principal: Principal):
    return {'personalization': personalization_enabled(principal.subject)}


@router.put('/preferences')
def save_preferences(body: Preferences, principal: Principal):
    with private_cursor(principal.subject, *TABLES) as c:
        c.execute('INSERT INTO momentum_preferences(owner_id,personalization) VALUES (%s,%s) ON CONFLICT(owner_id) DO UPDATE SET personalization=EXCLUDED.personalization',
                  (principal.subject,body.personalization))
    return body


@router.put('/{memory_id}')
def correct(memory_id: UUID, body: MemoryInput, principal: Principal):
    with private_cursor(principal.subject, *TABLES) as c:
        row = require_row(c.execute(f"UPDATE momentum_memories SET content=%s,status='pending',updated_at=now() WHERE id=%s AND owner_id=%s RETURNING {FIELDS}",
                                   (body.content,memory_id,principal.subject)).fetchone())
        audit(c,principal.subject,'memory.corrected',memory_id)
        return row


@router.post('/{memory_id}/approve')
def approve(memory_id: UUID, principal: Principal):
    with private_cursor(principal.subject, *TABLES) as c:
        row = require_row(c.execute(f'SELECT {FIELDS} FROM momentum_memories WHERE id=%s AND owner_id=%s FOR UPDATE', (memory_id,principal.subject)).fetchone())
        if row['status'] == 'approved':
            return row
        row = c.execute(f"UPDATE momentum_memories SET status='approved',updated_at=now() WHERE id=%s AND owner_id=%s RETURNING {FIELDS}", (memory_id,principal.subject)).fetchone()
        audit(c,principal.subject,'memory.approved',memory_id)
        return row


@router.delete('/{memory_id}', status_code=204)
def forget(memory_id: UUID, principal: Principal):
    with private_cursor(principal.subject, *TABLES) as c:
        require_row(c.execute('DELETE FROM momentum_memories WHERE id=%s AND owner_id=%s RETURNING id', (memory_id,principal.subject)).fetchone())
        audit(c,principal.subject,'memory.deleted',memory_id)
    return Response(status_code=204)


def personalization_enabled(owner):
    with private_cursor(owner, 'momentum_preferences') as c:
        row = c.execute('SELECT personalization FROM momentum_preferences WHERE owner_id=%s',(owner,)).fetchone()
        return row['personalization'] if row else True


def relevant_memories(owner, query):
    words = set(re.findall(r'\w{3,}', query.casefold()))
    with private_cursor(owner,'momentum_memories') as c:
        rows = c.execute("SELECT content FROM momentum_memories WHERE owner_id=%s AND status='approved' ORDER BY updated_at DESC LIMIT 100", (owner,)).fetchall()
    ranked = [(len(words & set(re.findall(r'\w{3,}',r['content'].casefold()))),r['content']) for r in rows]
    return [content for score,content in sorted(ranked,key=lambda x:x[0],reverse=True) if score > 0][:5]
