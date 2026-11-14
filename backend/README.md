# Momentum AI API

FastAPI with verified Neon Auth JWTs, Psycopg transactions, owner filters and forced
PostgreSQL RLS. Gemini stays behind the planning provider interface.

See the [root setup guide](../README.md) and [migration instructions](migrations/README.md).
`python -m app.schema_audit` reads catalog metadata and reports missing private
tables, active RLS and grants; it does not apply migrations or inspect user records.
`GET /health/live` reports process liveness only.

The optional push worker dependency is installed with `pip install '.[push]'`.
Run `python -m app.reminder_worker` once per minute using a dedicated scheduler
login and `REMINDER_DATABASE_URL`. It runs one bounded batch and exits. Supervise
this command outside the web process; do not schedule from a browser tab.

AI request budgets are currently 20/hour and 100/day per verified user. Failed
requests and retries can consume quota. Output is bounded to 4096 provider tokens;
provider requests have a 45-second timeout. These controls are not a global billing
cap; configure provider budgets and alerts separately.

The account export API returns allowlisted sections in pages of 200 rows. Every
page requires authentication and active RLS. Authentication records, push credentials
and external-provider records are excluded. Concurrent changes can affect page consistency.
