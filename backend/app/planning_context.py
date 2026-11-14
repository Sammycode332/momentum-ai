from datetime import date
from typing import Any

from psycopg.rows import dict_row

from app.goals import goals_connection
from app.onboarding import onboarding_connection, read_onboarding
from app.records import records_connection

# Static SQL only. Bound dates, status and recency prioritize current work.
RECORD_QUERIES = {
    "projects": """
        SELECT id, left(name, 160) AS name, status, deadline
        FROM public.momentum_projects WHERE owner_id = %s AND status <> 'completed'
        ORDER BY (status = 'paused'), deadline NULLS LAST, updated_at DESC, id LIMIT 8
    """,
    "tasks": """
        SELECT id, left(title, 160) AS title, status, priority, due_date, project_id
        FROM public.momentum_tasks WHERE owner_id = %s AND status <> 'completed'
        ORDER BY (status = 'paused'), due_date NULLS LAST,
            CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
            updated_at DESC, id LIMIT 12
    """,
    "learning": """
        SELECT left(subject, 160) AS subject, left(objective, 200) AS objective, progress_status
        FROM public.momentum_learning WHERE owner_id = %s AND progress_status <> 'completed'
        ORDER BY (progress_status = 'paused'), updated_at DESC, id LIMIT 5
    """,
    "academics": """
        SELECT left(activity, 160) AS activity, status, deadline
        FROM public.momentum_academics WHERE owner_id = %s AND status <> 'completed'
        ORDER BY (status = 'paused'), deadline NULLS LAST, updated_at DESC, id LIMIT 5
    """,
    "opportunities": """
        SELECT left(name, 160) AS name, left(type, 80) AS type, status, application_deadline
        FROM public.momentum_opportunities WHERE owner_id = %s AND status <> 'completed'
        ORDER BY (status = 'paused'), application_deadline NULLS LAST, updated_at DESC, id LIMIT 5
    """,
}


def load_planning_context(owner: str) -> dict[str, Any]:
    context: dict[str, Any] = {"server_date": date.today().isoformat()}
    with records_connection(owner) as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            for domain, query in RECORD_QUERIES.items():
                context[domain] = cursor.execute(query, (owner,)).fetchall()
    with goals_connection(owner) as connection:
        context["goals"] = [title for (title,) in connection.execute(
            """SELECT left(title, 160) FROM public.momentum_goals WHERE owner_id = %s AND NOT completed
            ORDER BY created_at DESC, id LIMIT 5""", (owner,),
        ).fetchall()]
    with onboarding_connection(owner) as connection:
        preferences = read_onboarding(connection, owner)
    if preferences and preferences.status == "completed":
        context["primary_focus"] = preferences.primary_focus
    return context
