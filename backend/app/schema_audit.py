"""Read-only catalog inspection. Never selects application rows or applies migrations."""
import json

from app.database import DatabaseConfigurationError, DatabaseError, database_connection

TABLES = (
    "momentum_goals", "momentum_onboarding", "momentum_projects", "momentum_tasks",
    "momentum_learning", "momentum_academics", "momentum_opportunities",
    "momentum_conversations", "momentum_conversation_messages",
    "momentum_preferences", "momentum_memories", "momentum_audit",
    "momentum_practice", "momentum_practice_answers", "momentum_reminders",
    "momentum_notifications", "momentum_actions", "momentum_ai_usage",
    "momentum_push_subscriptions", "momentum_push_deliveries",
)


def main():
    try:
        with database_connection() as connection:
            connection.execute("SET TRANSACTION READ ONLY")
            role = connection.execute(
                "SELECT current_user, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
            ).fetchone()
            tables = connection.execute("""
                SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity,
                       row_security_active(c.oid),
                       has_table_privilege(c.oid, 'SELECT'),
                       has_table_privilege(c.oid, 'INSERT'),
                       has_table_privilege(c.oid, 'UPDATE'),
                       has_table_privilege(c.oid, 'DELETE'),
                       (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid)
                FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = ANY(%s)
                ORDER BY c.relname
            """, (list(TABLES),)).fetchall()
            print(json.dumps({
                "role": role[0], "superuser": role[1], "bypass_rls": role[2],
                "tables": [dict(zip(("table", "rls", "force_rls", "active_rls", "select",
                                      "insert", "update", "delete", "policy_count"), row)) for row in tables],
                "missing": sorted(set(TABLES) - {row[0] for row in tables}),
            }, indent=2))
            return 0 if len(tables) == len(TABLES) and not any(role[1:]) and all(row[3] for row in tables) else 1
    except (DatabaseConfigurationError, DatabaseError):
        print("Schema audit unavailable; check local configuration and connectivity. No migrations applied.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
