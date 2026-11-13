# Personal Goals migration

In the Neon SQL Editor, select the intended development branch and database. Run [001_personal_goals.sql](001_personal_goals.sql) once as the migration role. The SQL creates the application-owned table and policies in one transaction. It does not touch the Neon Auth schema.

Use an application role without superuser or `BYPASSRLS` privileges. When it differs from the migration role, grant it `USAGE` on schema `public` and `SELECT, INSERT` on `public.momentum_goals`. Use that role's URI for the backend's `DATABASE_URL`. The API refuses Goals operations if RLS is inactive for the runtime role.

Before deploying, validate the migration on a disposable database. Apply the same migration there, set `GOALS_TEST_DATABASE_URL` in the backend test process to that database's runtime-role URI, and run `python -m pytest tests/test_goals_postgres.py` from the backend. The policy test rolls back its synthetic writes.

If application deployment must be reversed, roll back the application first and leave the table in place to preserve goals. Revert schema changes on a disposable branch or follow a reviewed backup and restore procedure for any database containing user data.
