"""Public Remotive browsing. Never require signup to see source listings."""
from datetime import datetime, UTC, timedelta
from uuid import uuid4
from urllib.parse import urlparse
import json
import httpx
from fastapi import APIRouter, Query
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict
from app.database import database_connection, DatabaseError, DatabaseConfigurationError
from app.private_store import Principal, private_cursor, require_row
from app.api_errors import ApiError

router=APIRouter(prefix='/api/v1/discovery',tags=['public opportunity discovery'])


def normalize_jobs(jobs):
    result=[];seen=set()
    for job in jobs[:10000]:
        if not isinstance(job,dict):continue
        url=job.get('url','');parsed=urlparse(url if isinstance(url,str) else '')
        if parsed.scheme!='https' or parsed.hostname not in ('remotive.com','www.remotive.com') or parsed.username or parsed.password:continue
        if url in seen:continue
        title=job.get('title');location=job.get('candidate_required_location','Not specified')
        if not isinstance(title,str) or not title.strip():continue
        seen.add(url)
        result.append({'id':str(job.get('id',''))[:100],'title':title[:200],'url':url[:2048],
                       'organization':str(job.get('company_name',''))[:200],
                       'location':str(location)[:300],'category':'internships' if job.get('job_type')=='internship' else 'jobs',
                       'specialty':str(job.get('category',''))[:120], 'remote':True,
                       'published_at':str(job.get('publication_date',''))[:50], 'deadline':None,'source':'Remotive'})
    return result


def source_snapshot():
    now=datetime.now(UTC)
    try:
        with database_connection() as conn:
            with conn.cursor(row_factory=dict_row) as c:
                # Shared DB cache enforces the source's recommended max four fetches/day across workers.
                c.execute("SELECT pg_advisory_xact_lock(hashtextextended('momentum.remotive.cache',0))")
                row=c.execute("SELECT payload,fetched_at,next_fetch FROM momentum_source_cache WHERE source='remotive'").fetchone()
                if not row:raise DatabaseError('Missing source cache')
                if row['next_fetch']<=now:
                    try:
                        with httpx.stream('GET','https://remotive.com/api/remote-jobs',timeout=12,follow_redirects=False) as response:
                            response.raise_for_status();raw=bytearray()
                            for chunk in response.iter_bytes():
                                raw.extend(chunk)
                                if len(raw)>8_000_000:raise ValueError('Source too large')
                        jobs=normalize_jobs(json.loads(raw).get('jobs',[]))
                        c.execute("UPDATE momentum_source_cache SET payload=%s,fetched_at=%s,next_fetch=%s WHERE source='remotive'",(Jsonb(jobs),now,now+timedelta(hours=6)))
                        return jobs,now,False
                    except (httpx.HTTPError,ValueError,TypeError,AttributeError):
                        c.execute("UPDATE momentum_source_cache SET next_fetch=%s WHERE source='remotive'",(now+timedelta(hours=6),))
                return row['payload'],row['fetched_at'],row['fetched_at'] is None or now-row['fetched_at']>timedelta(hours=24)
    except (DatabaseError,DatabaseConfigurationError):
        raise ApiError(503,'DISCOVERY_UNAVAILABLE','Opportunity discovery is unavailable. Try again later.') from None


@router.get('')
def discover(q: str=Query('',max_length=100),location: str=Query('',max_length=100),category: str=Query('jobs',max_length=30)):
    if category not in ('jobs','internships'):
        return {'items':[],'supported':False,'message':'A verified source for this category has not been connected. No listings have been generated.'}
    jobs,fetched,stale=source_snapshot()
    if fetched is None:
        raise ApiError(503,'SOURCE_UNAVAILABLE','The opportunity source is unavailable. Please try again later.')
    words=q.casefold().split();matches=[]
    for job in jobs:
        haystack=f"{job['title']} {job['organization']} {job['specialty']}".casefold()
        if job['category']!=category or not all(word in haystack for word in words):continue
        if location and location.casefold() not in job['location'].casefold():continue
        matches.append({**job,'match_reason':f"Matches your search '{q}' in the title, organization or category." if q else 'Listed by Remotive in your selected category.'})
    return {'items':matches[:50],'supported':True,'fetched_at':fetched,'stale':stale,
            'message':'Source: Remotive. Listings are delayed by 24 hours. Eligibility and deadlines must be checked on the source page.'}


class Save(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id: str


@router.post('/save',status_code=201)
def save(body: Save,principal: Principal):
    jobs,_,stale=source_snapshot()
    if stale:raise ApiError(409,'SOURCE_STALE','Refresh discovery before saving this listing.')
    job=next((j for j in jobs if j['id']==body.id),None)
    if not job:raise ApiError(404,'LISTING_UNAVAILABLE','This listing is no longer in the source feed.')
    with private_cursor(principal.subject,'momentum_opportunities') as c:
        c.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(principal.subject,))
        existing=c.execute('SELECT id FROM momentum_opportunities WHERE owner_id=%s AND url=%s',(principal.subject,job['url'])).fetchone()
        if existing:return existing
        return c.execute("INSERT INTO momentum_opportunities(id,owner_id,name,type,status,url) VALUES (%s,%s,%s,%s,'not_started',%s) RETURNING id",(uuid4(),principal.subject,job['title'],job['category'],job['url'])).fetchone()
