"""Ground explicit workspace lookups in the signed-in user's saved records."""

import re
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.private_store import private_cursor

LIMIT = 10
INTENTS = (
    ("today", r"\bmy tasks?\b.*\btoday\b|\btasks?\b.*\b(?:i have|i need to|due)\b.*\btoday\b|\btoday(?:'s)?\s+tasks\b"),
    ("unfinished", r"\b(?:unfinished|incomplete|open|pending|outstanding) tasks\b|\btasks\b.*\b(?:unfinished|left to do)\b"),
    ("deadlines", r"\bupcoming deadlines\b|\bdeadlines\b.*\b(?:coming up|this week|next seven days)\b"),
    ("milestones", r"\bmilestones?\b.*\b(?:status|progress|completed|done|outstanding|in progress)\b|\b(?:status|progress|completed|done|outstanding|in progress)\b.*\bmilestones?\b"),
    ("goals", r"\bprogress\w*\b.*\bgoals?\b|\bgoal progress\b|\bmy goals\b.*\bprogress\w*\b"),
    ("projects", r"\bprojects?\b.*\b(?:attention|at risk|overdue)\b"),
)
LOOKUP = re.compile(r"^(?:please[, ]+)?(?:what|which|how am i|how (?:are|is) my|show|list|tell me|"
                    r"(?:can|could) you (?:show|list|tell)|today's tasks|unfinished tasks|upcoming deadlines|goal progress)\b", re.I)


def workspace_intent(message: str) -> str | None:
    if not LOOKUP.match(message):
        return None
    return next((intent for intent, pattern in INTENTS if re.search(pattern, message, re.I)), None)


def markdown_label(value: str) -> str:
    return re.sub(r"([\\`*_{}\[\]()<>#+.!|~-])", r"\\\1", " ".join(value.split())[:150])


def workspace_answer(intent: str, owner: str, timezone: str) -> str:
    today = datetime.now(UTC).astimezone(ZoneInfo(timezone)).date()
    end = today + timedelta(days=6)
    if intent in {"today", "unfinished"}:
        condition = "due_date = %s" if intent == "today" else "status <> 'completed'"
        args = (owner, today, LIMIT + 1) if intent == "today" else (owner, LIMIT + 1)
        with private_cursor(owner, "momentum_tasks") as cursor:
            rows = cursor.execute(
                f"""SELECT title, status, priority, due_date FROM public.momentum_tasks
                WHERE owner_id = %s AND {condition}
                ORDER BY due_date NULLS LAST, CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
                         updated_at DESC, id LIMIT %s""", args,
            ).fetchall()
        heading = f"Tasks due today ({today})" if intent == "today" else "Unfinished tasks"
        lines = [
            f"{markdown_label(row['title'])} · {row['status'].replace('_', ' ')} · {row['priority']} priority"
            + (f" · due {row['due_date']}" if row["due_date"] else "")
            for row in rows[:LIMIT]
        ]
    elif intent == "deadlines":
        with private_cursor(owner, "momentum_tasks", "momentum_projects", "momentum_academics",
                            "momentum_opportunities") as cursor:
            rows = cursor.execute(
                """SELECT title, due, kind FROM (
                    SELECT id, title, due_date AS due, 'Task' AS kind FROM public.momentum_tasks
                    WHERE owner_id = %(owner)s AND status <> 'completed' AND due_date BETWEEN %(start)s AND %(end)s
                    UNION ALL
                    SELECT id, name, deadline, 'Project' FROM public.momentum_projects
                    WHERE owner_id = %(owner)s AND status <> 'completed' AND deadline BETWEEN %(start)s AND %(end)s
                    UNION ALL
                    SELECT id, activity, deadline, 'Academic' FROM public.momentum_academics
                    WHERE owner_id = %(owner)s AND status <> 'completed' AND deadline BETWEEN %(start)s AND %(end)s
                    UNION ALL
                    SELECT id, name, application_deadline, 'Opportunity' FROM public.momentum_opportunities
                    WHERE owner_id = %(owner)s AND status <> 'completed'
                      AND application_stage NOT IN ('accepted', 'rejected', 'withdrawn')
                      AND application_deadline BETWEEN %(start)s AND %(end)s
                ) AS deadlines ORDER BY due, kind, title, id LIMIT %(limit)s""",
                {"owner": owner, "start": today, "end": end, "limit": LIMIT + 1},
            ).fetchall()
        heading = f"Upcoming deadlines ({today} through {end})"
        lines = [f"{row['due']} · {row['kind']} · {markdown_label(row['title'])}" for row in rows[:LIMIT]]
    elif intent == "milestones":
        with private_cursor(owner, "momentum_goals", "momentum_tasks") as cursor:
            rows = cursor.execute(
                """SELECT t.title, t.kind, t.status, g.title AS goal
                FROM public.momentum_tasks t
                JOIN public.momentum_goals g ON g.id = t.goal_id AND g.owner_id = t.owner_id
                WHERE t.owner_id = %s ORDER BY t.due_date NULLS LAST, t.kind, t.id LIMIT %s""",
                (owner, LIMIT + 1),
            ).fetchall()
        heading = "Saved milestones and linked tasks"
        lines = [
            f"{markdown_label(row['title'][:65])} · {row['kind']} · {row['status'].replace('_', ' ')}"
            f" · {markdown_label(row['goal'][:65])}" for row in rows[:LIMIT]
        ]
    elif intent == "goals":
        with private_cursor(owner, "momentum_goals", "momentum_tasks") as cursor:
            rows = cursor.execute(
                """SELECT g.title, g.completed, progress.done, progress.total,
                    progress.milestones_done, progress.milestones, progress.in_progress
                FROM (
                    SELECT id, owner_id, title, completed, created_at FROM public.momentum_goals
                    WHERE owner_id = %s ORDER BY completed, created_at DESC, id LIMIT %s
                ) AS g
                CROSS JOIN LATERAL (
                    SELECT count(*) FILTER (WHERE status = 'completed') AS done, count(*) AS total,
                        count(*) FILTER (WHERE kind = 'milestone' AND status = 'completed') AS milestones_done,
                        count(*) FILTER (WHERE kind = 'milestone') AS milestones,
                        count(*) FILTER (WHERE status = 'in_progress') AS in_progress
                    FROM public.momentum_tasks WHERE owner_id = g.owner_id AND goal_id = g.id
                ) AS progress ORDER BY g.completed, g.created_at DESC, g.id""", (owner, LIMIT + 1),
            ).fetchall()
        heading = "Goal progress"
        lines = [
            f"{markdown_label(row['title'])} · goal {'complete' if row['completed'] else 'open'} · "
            + (f"{row['done']} of {row['total']} linked tasks complete" if row["total"] else "no linked tasks")
            + (f" · {row['in_progress']} in progress · {row['total'] - row['done'] - row['in_progress']} outstanding"
               if row["total"] else "")
            + (f" · {row['milestones_done']} of {row['milestones']} milestones complete" if row["milestones"] else "")
            for row in rows[:LIMIT]
        ]
    else:
        with private_cursor(owner, "momentum_projects", "momentum_tasks") as cursor:
            rows = cursor.execute(
                """SELECT p.name, p.deadline, p.status, work.overdue
                FROM public.momentum_projects p
                CROSS JOIN LATERAL (
                    SELECT count(*) AS overdue FROM public.momentum_tasks
                    WHERE owner_id = p.owner_id AND project_id = p.id AND status <> 'completed' AND due_date < %s
                ) AS work
                WHERE p.owner_id = %s AND p.status <> 'completed'
                AND (p.deadline <= %s OR work.overdue > 0 OR p.status = 'paused')
                ORDER BY (work.overdue > 0 OR coalesce(p.deadline < %s, false)) DESC,
                         p.deadline NULLS LAST, work.overdue DESC, p.id LIMIT %s""",
                (today, owner, end, today, LIMIT + 1),
            ).fetchall()
        heading = "Projects needing attention"
        lines = [
            f"{markdown_label(row['name'])} · {row['status'].replace('_', ' ')}"
            + (f" · deadline {row['deadline']}" if row["deadline"] else "")
            + (f" · {row['overdue']} overdue tasks" if row["overdue"] else "")
            for row in rows[:LIMIT]
        ]
    details = "\n".join(f"- {line}" for line in lines) or "No saved records match this view."
    if len(rows) > LIMIT:
        details += f"\n\nShowing the first {LIMIT} matching records."
    return f"### {heading}\n\n{details}"
