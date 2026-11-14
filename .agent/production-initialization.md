# Production initialization — 2026-11-14

Target is Momentum AI project `noisy-art-71570229`, branch `production`
(`br-wild-fog-bapicvv8`), database `neondb`. The owner reported a successful
read-only inspection as `neondb_owner`, with nine `neon_auth` catalog tables,
zero `public.momentum_*` tables and none of the three expected Momentum roles.
All 14 migrations have missing effects on this baseline. The catalog does not
establish historical attempts or rollbacks. The repository documents development
recovery only. Production Auth account and workspace rows were outside the audit.

## Rehearsal evidence

The fresh local PostgreSQL 18.7 rehearsal committed 001–014 and the separate
role, base-grant and runtime LOGIN checkpoints. The restricted runtime had active
RLS on 20 private tables. Scoped grants, cache seed and unset-owner access
checks passed. All 32 focused tests passed with synthetic fixtures. The local
run used SQL to set a temporary runtime password.

The owner chose to proceed using the local rehearsal. Neon-managed password
generation and fresh pooled login will be checked at the production runtime
credential checkpoint after approval. Stop if either operation fails.

## Preflight and recovery point

1. After approval, reconfirm the project, branch ID, database, and Console-issued
   direct endpoint. Rerun the approved read-only catalog and stop if the baseline
   changed. Check the server major version is at least 15 for the column-specific
   `ON DELETE SET NULL` syntax in 003 and 008. Verify the schema owner can create
   roles and objects. Confirm the effective search path resolves unqualified
   migration objects to `public`, with no temporary or alternate schema shadowing.
2. The production Backup & Restore page showed a six-hour history window and
   no snapshots. Use the available point-in-time recovery window for this
   initialization. Immediately before the first write, record an exact UTC
   timestamp and verify it is selectable in the restore window. Retain the
   timestamp with the migration log. A restore requires separate approval.
   [Neon instant restore](https://neon.com/docs/postgres/backup-restore/branch-restore)
3. Record the reviewed Git revision and SHA-256 of each migration in
   `backend/migrations`. Run each file as its own transaction using the schema
   owner. Use a client that stops on the first SQL error. Check every committed
   result from a fresh connection and log it externally by branch ID, time and
   file hash. On failure, roll back the current transaction, inspect the last
   committed checkpoint and resume only once the cause is understood.

## Exact order

Start with a separate transaction creating the restricted application role:

```sql
BEGIN;
CREATE ROLE momentum_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
    NOREPLICATION NOBYPASSRLS;
COMMIT;
```

Verify the committed role. After 014 and the catalog checks, set a generated
credential through Neon Console **Roles → momentum_app → Reset password** for
the existing role, then enable LOGIN in a separate transaction using
`ALTER ROLE momentum_app LOGIN;`. Stop on any error, including `XX000`.
Verify effective privileges and
fresh pooled login. Save the production credential securely for the later
hosting secret store. SQL-created roles allow selective grants.
[Neon roles](https://neon.com/docs/manage/roles)

All rows below have **missing schema effects and are required** on the supplied
production baseline. The extra grants checkpoint follows 004.

| Order | File | Expected effect and checks |
| --- | --- | --- |
| 1 | `001_personal_goals.sql` | Goals, owner index, forced RLS, owner read/insert policies. |
| 2 | `002_user_onboarding.sql` | Onboarding, forced RLS and owner read/insert/update policies. |
| 3 | `003_core_records.sql` | Projects, tasks, learning, academics and opportunities with owner RLS and same-owner task/project linkage. |
| 4 | `004_conversations.sql` | Conversations and messages with sequence constraints, same-owner FK and RLS. |
| 4a | Base grants below | Runtime grants for 001–004 live in the migration README. |
| 5 | `005_goal_lifecycle.sql` | `completed`, owner update/delete policies and restricted column update grants. |
| 6 | `006_personal_memory.sql` | Preferences, memories and audit with owner RLS. |
| 7 | `007_practice.sql` | Practice and answers with same-owner FK and RLS. |
| 8 | `008_task_relationships.sql` | Goal/parent links, milestone kind, same-owner constraints and relationship indexes. |
| 9 | `009_reminders.sql` | Corrected file validates the scheduler group, adds preferences, reminder/inbox tables, policies and grants. Commit the scheduler role separately immediately before this file. |
| 10 | `010_action_proposals.sql` | Original action table, status check, owner RLS and grants. |
| 11 | `011_runtime_services.sql` | Discovery cache and `remotive` seed, AI usage, push subscriptions and deliveries. Shared cache has restricted grants. User-owned tables have forced RLS. |
| 12 | `012_push_owner_integrity.sql` | Validated same-owner push foreign keys, notification uniqueness and delivery/subscription indexes. |
| 13 | `013_opportunity_pipeline.sql` | `application_stage` check/default and pipeline index. |
| 14 | `014_action_reversal.sql` | Replace the status constraint to include `reverted`, add `reverted_at`. |

Base grants, committed as a separate checkpoint:

```sql
BEGIN;
GRANT CONNECT ON DATABASE neondb TO momentum_app;
GRANT USAGE ON SCHEMA public TO momentum_app;
GRANT SELECT, INSERT ON public.momentum_goals TO momentum_app;
GRANT SELECT, INSERT, UPDATE ON public.momentum_onboarding TO momentum_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.momentum_projects,
    public.momentum_tasks, public.momentum_learning, public.momentum_academics,
    public.momentum_opportunities TO momentum_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.momentum_conversations TO momentum_app;
GRANT SELECT, INSERT ON public.momentum_conversation_messages TO momentum_app;
COMMIT;
```

Scheduler role checkpoint immediately before 009:

```sql
BEGIN;
CREATE ROLE momentum_scheduler NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
    NOREPLICATION NOBYPASSRLS;
COMMIT;
```

Verify its flags and confirm `momentum_app` is outside the scheduler group.
Corrected 009 checks for the existing role and proceeds without duplicate
creation. The worker login is a separate future activation. The existing
scheduler authentication blocker remains open.

Development already had 001–004, 008 and 013 and received the final 014 action
shape during its repaired 010. Fresh production uses each original file in
numeric order. Treat the files as non-idempotent. They create named objects and
policies, add columns, and in 011 insert a unique seed. File 014 drops and replaces
one check constraint inside its transaction. File 005 and later alter existing
application tables and may take locks. Foreign-key delete actions affect future
operations. The files contain no table drops, data deletes, truncations or Auth
schema changes.

## Auth and verification

Nine `neon_auth` tables establish that Auth storage is provisioned. Service
enablement, branch-specific Auth URL/JWKS, trusted origins, JWT validation and
the provider's advisory status are unverified. Inspect the production branch's
Better Auth settings and use that branch's values for `VITE_NEON_AUTH_URL`,
`NEON_AUTH_BASE_URL` and `NEON_AUTH_JWKS_URL`. Validate signing keys, issuer and
the exact hosting origin before a separately approved synthetic sign-in.
[Neon Auth React setup](https://neon.com/docs/auth/quick-start/react)

- Run `python -m app.schema_audit` as restricted `momentum_app`. Expect active RLS
  on 20 private tables. Separately verify the shared cache and its seed, all
  columns, defaults, validated constraints and indexes, effective table and
  column grants, object ownership, and role memberships against the reviewed
  files and development. Confirm PUBLIC lacks app table access and runtime has
  no schema CREATE privilege or administrative membership. Check access to
  `neon_auth` by grants without reading account rows.
- On a disposable same-version branch, run the existing real PostgreSQL goals,
  conversation, action and export fixtures with two synthetic owners. Extend
  coverage before launch to the remaining private domains. Verify absent-owner
  access is denied, legitimate owner CRUD succeeds, cross-user reads and writes
  fail at SQL and API layers, and cross-owner links fail. Validate scheduler
  grants at catalog level. Exercise worker delivery once separately approved.
- On production, start with catalog and restricted connection checks. Use a
  separately approved synthetic live smoke test to verify Auth and hosting.
  Keep live traffic off while these gates are open.

## Rollback and approval boundary

A failed migration rolls back its own transaction. Keep earlier committed
checkpoints for diagnosis and correct forward where safe. After an app rollout,
roll back the app first and retain compatible schema. For a branch-level recovery,
freeze writes, verify the recovery point on a separate branch, reconcile any
newer writes and account/session changes, and obtain approval before a restore
or cutover. Restoring a production branch may affect all its databases and Auth
state. [Neon instant restore](https://neon.com/docs/postgres/backup-restore/branch-restore)

After preflight passes, request approval for role creation, base grants, the
14 migrations, the restricted runtime credential and LOGIN checkpoint, and
read-only verification on `production/neondb`. A branch restore, Auth changes,
worker activation and Render deployment require separate approval.
