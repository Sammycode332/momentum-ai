# Momentum AI

Turn your goals into progress with a personal workspace for projects, learning,
academics, opportunities and an AI assistant.

**Development release, not production-certified.** See the
[feature inventory and release gates](.agent/release-plan.md) for verified status.

## Local setup

Requirements: Node.js 24, Python 3.13, a Neon development database and Neon Auth.

1. Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to
   `frontend/.env`. Configure values locally; never commit credentials.
2. Use the restricted `momentum_app` connection for `DATABASE_URL`.
   A separate schema owner applies outstanding migrations; see
   [migration instructions](backend/migrations/README.md). Do not rerun successful migrations.
3. From `backend`, create a virtual environment if needed, then run:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install '.[test]'
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
   ```

4. In another terminal, from `frontend`:

   ```powershell
   npm ci
   npm run dev
   ```

The frontend proxies `/api` to port 8001 by default. For a different backend,
set `MOMENTUM_DEV_API_TARGET` before starting Vite. Register the local frontend
origin in Neon Auth's trusted origins. `VITE_NEON_AUTH_URL` is public configuration;
Gemini and database secrets belong only in the backend environment.

## Workspace

- AI Assistant contains Chat, Learn, Interview and Approvals modes.
- Learning holds saved learning activities; guided practice is in the assistant.
- Opportunities contains saved records and public Remotive discovery.
- Settings contains profile, approved AI memory and Data & support.
- Notifications contains reminder scheduling, quiet hours and device push controls.

Export downloads are private JSON files. Full Neon account deletion is unfinished.
Push requires additional configuration and a running worker. See the
[deployment and operations guide](.agent/deployment.md).

## Checks

```powershell
# backend
.\.venv\Scripts\python.exe -m pytest -q
# frontend
npm test
npm run lint
npm run build
```

PostgreSQL isolation tests need dedicated disposable test databases. A skipped
test does not establish isolation. CI runs mocked tests and builds; it does not
deploy or access production credentials.

## Engineering documentation

- [Architecture](.agent/architecture.md), [decisions](.agent/decisions.md)
- [Progress and evidence](.agent/progress.md), [bugs](.agent/bugs.md)
- [Release checklist](.agent/release-checklist.md)
- [Privacy and terms drafts for review](.agent/privacy-terms-draft.md)
