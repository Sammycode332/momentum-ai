# Environment, Configuration, and Secrets Conventions

## Isolated local diagnosis

Default Vite development proxy remains `http://127.0.0.1:8001`. To test a separate backend without stopping an existing instance, set server-process `MOMENTUM_DEV_API_TARGET=http://127.0.0.1:8002`, run Uvicorn on port 8002, and run Vite on the existing trusted frontend port. This variable is not exposed through a `VITE_` prefix. Bind Vite to IPv4 loopback if localhost IPv6 is unreachable, but continue browsing the trusted `http://localhost:5173` origin. Do not change authentication trusted origins to work around verification failures.

This document establishes the FND-02 configuration boundary. It does not select a hosting provider, secret manager, AI provider, or runtime configuration library.

## Repository convention

Real environment files are ignored throughout the repository: `.env` and `.env.*`. Placeholder-only templates named `.env.example` or `.env.*.example` may be committed. Templates must contain no real credentials, project URLs, tokens, or environment-specific values.

Do not place secrets in source files, documentation examples, build artifacts, prompts, logs, error messages, or committed environment files. If a secret is accidentally committed, treat it as exposed: revoke or rotate it through the owning service and remove it through the approved incident/repository procedure.

## Environment use

### Local development

Developers may supply configuration through ignored environment files or process environment variables. The frontend's Vite tooling can load its supported `.env` files. The backend loads its ignored local `.env` file for the Neon Auth verification settings without overriding process-managed values.

Neon Auth session cookies are managed by Neon Auth. For local browser authentication, configure the exact frontend origin in Neon Auth's trusted origins (including scheme, host, and port, such as `http://localhost:5173`). `localhost` and `127.0.0.1` are different origins. If the configured origin is not trusted or the browser rejects the session cookie, a successful credential request cannot survive the SDK's session refresh; application code must not replace that cookie with a token stored in browser storage.

When Neon Auth requires email verification, it creates an unverified user and delays session creation. This Neon Auth branch sends verification codes (OTP), so the frontend submits the email and code through the official client rather than relying on a callback URL. The branch must keep email/password authentication, required verification, an email provider, and the exact trusted frontend origin configured. These provider settings are not stored in this repository.

### Staging and production

The eventual hosting environment injects runtime configuration and secrets. They are configured separately for each environment and are never copied into the repository. This convention deliberately does not select a host, deployment platform, secret manager, or environment naming scheme beyond local, staging, and production.

## Public browser configuration

In Vite, variables with the `VITE_` prefix are available to browser code through `import.meta.env`. Treat every `VITE_*` value as public: it can be present in the compiled client bundle and visible to users. Use this prefix only for non-sensitive client configuration, such as a future public API base URL.

Never use `VITE_*` for credentials, private tokens, AI API keys, database credentials, signing secrets, or other privileged material. Frontend visibility and route guards are not authorization controls.

The Neon Auth URL is public browser configuration. It may be present in a `VITE_*` variable, but a browser session or token is never authorization proof for backend or database access until verified server-side and protected with RLS where applicable.

## Backend-only configuration

For the ID-02 connectivity check, open **Connect** in the Neon console and select the development branch, database, and a least-privileged role that can connect. Copy its PostgreSQL connection URI, including the database name and password, into `DATABASE_URL` in the ignored `backend/.env` or inject it into the backend process environment. The process environment takes precedence. Keep this value out of frontend files, `VITE_*` variables, and source control.

From `backend/` with the virtual environment active, run `python -m pip install -e ".[test]"` and then `python -m app.database`. The check prints a generic result and exits with code 0 for success, 1 for a failed check, or 2 for missing or invalid configuration.

Neon Auth JWKS and Auth base URLs, privileged database credentials, AI-provider API keys, database credentials, signing secrets, and server-only service endpoints are backend runtime configuration. Backend code must read only the configuration it needs, validate required values when that code is implemented, and avoid returning or logging values.

Choosing a backend settings library, dotenv loader, secret manager, provider SDK, exact variable names, or deployment integration is deferred until a feature needs it. Any later choice must preserve this public/private boundary and be recorded through the project decision process.

## Verification

When this convention changes, use `git check-ignore -v --no-index` to inspect the effective ignore rule for real environment paths and template exceptions. Confirm templates are trackable with `git ls-files --others --exclude-standard`. Inspect tracked filenames and the diff for accidental credential-bearing files or values, and run `git diff --check`.

### AI-01 live smoke test

1. Use a development account with synthetic productivity records. On the Neon development branch, confirm migrations 001–003 and their documented runtime grants are in place. Use the existing restricted backend role.
2. In the ignored `backend/.env` or backend process environment, configure both `GEMINI_API_KEY` and `GEMINI_MODEL`. The backend uses the explicitly configured model. Verify it is available to the key and the Gemini configuration is approved for the data sent to it before using real user records.
3. With a working Python environment, run `python -m pip install -e ".[test]"` and `python -m uvicorn app.main:app --host 127.0.0.1 --port 8001` from `backend/`. Run `npm run dev` from `frontend/` and open the trusted local Neon Auth origin.
4. Sign in, create a synthetic project and a linked high-priority task due today, and open AI Assistant. Send “Which of my tasks should I prioritize today, and why?” Check that the reply grounds its advice in the account’s records. Send “What should I do first if I only have 15 minutes?” to confirm the follow-up uses the preceding turns.
5. For a structured planning check, open Structured planner and generate a 30-minute plan. Check the time total, record references, and that the task and project are unchanged.
