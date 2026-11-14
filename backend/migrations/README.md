# Application migrations

## Verified development recovery — 2026-11-14

On project `noisy-art-71570229`, branch `br-spring-base-bao04hi8`, the base
grants for 001–004 and migrations 005, 006, 007, corrected 009, 011 and 012
were separately committed and checked from fresh connections. The actions table
was installed with 010 and the final 014 schema together, including `reverted_at`
and `reverted`. Never run standalone 014 on that recovered schema. Existing
008 and 013 were preserved. These facts supersede the earlier activation history below.

The backend now uses restricted `momentum_app`. The administrative connection
is kept in the ignored `backend/.env.recovery-admin`. `momentum_scheduler` is
`NOLOGIN`. Connectivity, the schema audit and synthetic PostgreSQL isolation
tests passed. Neon Auth branch ownership still needs confirmation.

## Migration 009: missing scheduler role recovery

The initial draft referenced `momentum_scheduler` without creating it. Corrected
009 creates a restricted **NOLOGIN** group before adding its policies/grants and
rejects a privileged existing role or app membership. No password/login is created.
Do not grant this role to `momentum_app`.

If original 009 failed with SQLSTATE 42704, run `ROLLBACK;` in the same SQL session
if it remains in an aborted transaction. On the intended development branch check
that `to_regclass('public.momentum_reminders')` and
`to_regclass('public.momentum_notifications')` both return null. If either exists,
inspect partial state first. Otherwise run the **entire corrected 009 once** as
the migration/schema owner with CREATEROLE. Leave successful 001–008 alone.
If CREATEROLE is denied, a role administrator must run the corrected migration;
do not elevate the runtime role. This migration is transactional.

Apply 006–008 before 009. 010 and 011 follow 009. These are development candidates
pending isolated PostgreSQL tests and live runtime validation.

## Goal lifecycle — migration 005 (prepared, not applied)

The goal lifecycle backend requires [005_goal_lifecycle.sql](005_goal_lifecycle.sql) **before that backend version starts**. It adds `completed` with an active/false default, owner-scoped update/delete policies and `UPDATE(title, completed), DELETE` grants for `momentum_app`. Existing IDs, titles and creation dates are preserved. The runtime role is not granted ownership changes, schema ownership or BYPASSRLS.

1. On an isolated test database, apply 001 and 005 as the schema owner (create the separate restricted runtime role first). Set only `GOALS_TEST_DATABASE_URL` to the test runtime URI and run `python -m pytest tests/test_goals_postgres.py`. The test rolls back synthetic data and now requires successful owner updates/deletes as well as cross-user denial.
2. Inspect the intended development branch for the `completed` column and `goals_update_own`/`goals_delete_own` policies. If 005 is already fully applied, do not rerun it. If state is inconsistent, investigate rather than running ad-hoc fixes.
3. Apply **only 005**, once, through the schema-owner connection. The migration is transactional and aborts if it cannot acquire locks within five seconds. Do not rerun migrations 001–004.
4. After validation, start the new backend and exercise edit, complete, reopen and delete using disposable goals. Confirm completed goals no longer appear in active-goal AI context.

Rollback: deploy the preceding application version and retain the additive schema/data. Do not drop the column or erase completion data as a routine rollback. Removal of policies/grants requires an explicitly scoped operational change. Production application is not authorized by the development workflow.

## Safe state inspection

Before applying anything, run `python -m app.schema_audit` with the configured runtime role. It reads catalog metadata only. On 2026-11-13, the audit found all nine expected tables, forced active RLS, and the documented restricted grants under `momentum_app` (not superuser, not BYPASSRLS). No migrations were rerun. Table presence is not a migration ledger or full schema-equivalence check. Preserve existing data and inspect constraints/policies before preparing any new migration.

In the Neon SQL Editor, select the intended development branch and database. Run [001_personal_goals.sql](001_personal_goals.sql) once as the migration role. The SQL creates the application-owned table and policies in one transaction. It does not touch the Neon Auth schema.

Use an application role without superuser or `BYPASSRLS` privileges. When it differs from the migration role, grant it `USAGE` on schema `public` and `SELECT, INSERT` on `public.momentum_goals`. Use that role's URI for the backend's `DATABASE_URL`. The API refuses Goals operations if RLS is inactive for the runtime role.

Before deploying, validate the migration on a disposable database. Apply the same migration there, set `GOALS_TEST_DATABASE_URL` in the backend test process to that database's runtime-role URI, and run `python -m pytest tests/test_goals_postgres.py` from the backend. The policy test rolls back its synthetic writes.

If application deployment must be reversed, roll back the application first and leave the table in place to preserve goals. Revert schema changes on a disposable branch or follow a reviewed backup and restore procedure for any database containing user data.

## User onboarding

Run [002_user_onboarding.sql](002_user_onboarding.sql) once in the Neon SQL Editor on the intended development database, after migration 001. Run it as the migration role. If the runtime role is separate, grant it `USAGE` on schema `public` and `SELECT, INSERT, UPDATE` on `public.momentum_onboarding`. Use the existing backend-only `DATABASE_URL` for the runtime role. The onboarding API requires active RLS.

## Core records

Run [003_core_records.sql](003_core_records.sql) once after migrations 001 and 002. For a separate runtime role, grant `USAGE` on schema `public` and `SELECT, INSERT, UPDATE, DELETE` on all five `momentum_*` tables created by this migration. The backend refuses operations unless RLS is active for every core-record table.

## Conversation history

Apply `004_conversations.sql` to the intended development branch after 001–003. As the migration role, grant the existing restricted runtime role:

```sql
GRANT USAGE ON SCHEMA public TO momentum_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.momentum_conversations TO momentum_app;
GRANT SELECT, INSERT ON public.momentum_conversation_messages TO momentum_app;
```

Deleting a conversation cascades to its messages. Roll back the application before removing grants. Retain tables containing user data unless an approved retention or restore procedure calls for removal.

To check RLS and cascade behavior, use the restricted role on an isolated database with migration 004 and set `CONVERSATIONS_TEST_DATABASE_URL`. Run `python -m pytest tests/test_conversation_history.py` from `backend/`. The PostgreSQL test rolls back its synthetic writes.

## Later feature migrations: application record

| Migration | Purpose | Activation evidence |
| --- | --- | --- |
| 006 | Preferences, approved memory, audit metadata | Local implementation; remote application unconfirmed |
| 007 | Tutoring/interview sessions and answers | Local implementation; remote application unconfirmed |
| 008 | Goal/task links, subtasks and milestones | Local implementation; remote application unconfirmed |
| 009 | Reminder/notification scheduling and scheduler role | Initial role error reported; corrected; successful retry unconfirmed |
| 010 | Approval-gated actions | Local implementation; remote application unconfirmed |
| 011 | Source cache, AI usage, push subscriptions/deliveries | Local implementation; remote application unconfirmed |
| 012 | Composite owner FKs and push indexes | Apply only after 011; remote application unconfirmed |

Account export and recovery add no migration. The 2026-11-14 read-only audit could not connect; it did not establish current remote state or apply SQL. Verify current state before any application; do not rerun successful files. Back up before schema changes and test on an isolated branch first.

## 013 — Opportunity application tracking (prepared, not applied)

Adds application_stage (saved/preparing/applied/interviewing/offered/accepted/rejected/withdrawn) separately from existing general status and adds an owner/stage/deadline index. Existing records default to saved; existing status/data is retained. Apply only once after inspecting current schema and after 001–012. This backend version's opportunity writes/export need the new column. Roll back code first and retain the additive column/data. The onboarding 503 diagnosed on 2026-11-14 is a rejected database credential, not a reason to rerun this or prior migrations.
