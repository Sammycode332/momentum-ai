"""Bounded, authenticated export. Subscription credentials are never exported."""
from fastapi import APIRouter, Query
from app.api_errors import ApiError
from app.private_store import Principal, private_cursor

router = APIRouter(prefix='/api/v1/account', tags=['account data'])
# Identifiers are constants, never interpolated from a request.
SECTIONS = {
    'goals': ('momentum_goals', 'id,title,completed,created_at', 'id'),
    'profile': ('momentum_onboarding', 'status,primary_focus,current_goals,planning_time', 'owner_id'),
    'projects': ('momentum_projects', 'id,name,description,status,deadline,created_at,updated_at', 'id'),
    'tasks': ('momentum_tasks', 'id,title,description,status,priority,due_date,project_id,goal_id,parent_id,kind,created_at,updated_at', 'id'),
    'learning': ('momentum_learning', 'id,subject,objective,progress_status,created_at,updated_at', 'id'),
    'academics': ('momentum_academics', 'id,activity,description,status,deadline,created_at,updated_at', 'id'),
    'opportunities': ('momentum_opportunities', 'id,name,type,status,application_stage,url,application_deadline,created_at,updated_at', 'id'),
    'conversations': ('momentum_conversations', 'id,title,updated_at', 'id'),
    'messages': ('momentum_conversation_messages', 'conversation_id,turn_id,position,role,content', 'conversation_id,position,role'),
    'memories': ('momentum_memories', 'id,content,status,created_at,updated_at', 'id'),
    'preferences': ('momentum_preferences', 'personalization,timezone,notifications_enabled,quiet_start,quiet_end', 'owner_id'),
    'practice': ('momentum_practice', 'id,kind,topic,level,format,curriculum,step,packet,version,created_at,updated_at', 'id'),
    'answers': ('momentum_practice_answers', 'id,session_id,version,answer,result,created_at', 'id'),
    'reminders': ('momentum_reminders', 'id,title,due_at,timezone,repeat,status,occurrence,created_at', 'id'),
    'notifications': ('momentum_notifications', 'id,reminder_id,occurrence,title,created_at,state,snoozed', 'id'),
    'actions': ('momentum_actions', 'id,proposal,status,result_id,created_at,applied_at,reverted_at', 'id'),
    'audit': ('momentum_audit', 'id,event,target_id,created_at', 'id'),
}
PAGE_SIZE = 200


@router.get('/export')
def export_manifest(principal: Principal):
    return {'sections': list(SECTIONS), 'page_size': PAGE_SIZE,
            'notice': 'Export excludes authentication and push credentials. Changes made during export may affect its consistency.'}


@router.get('/export/{section}')
def export_page(section: str, principal: Principal, offset: int = Query(0, ge=0, le=100000)):
    config = SECTIONS.get(section)
    if config is None:
        raise ApiError(404, 'EXPORT_SECTION_UNKNOWN', 'This export section is unavailable.')
    table, columns, order = config
    with private_cursor(principal.subject, table) as cursor:
        rows = cursor.execute(f'SELECT {columns} FROM {table} WHERE owner_id=%s ORDER BY {order} LIMIT %s OFFSET %s',
                              (principal.subject, PAGE_SIZE + 1, offset)).fetchall()
    return {'items': rows[:PAGE_SIZE], 'next_offset': offset + PAGE_SIZE if len(rows) > PAGE_SIZE else None}
