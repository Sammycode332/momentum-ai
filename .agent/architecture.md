# Technical Architecture

CORE-03 adds goal lifecycle PATCH/DELETE and a completion flag through migration 005 (prepared, not applied as of this checkpoint). Only incomplete goals enter the active-goal AI context. This application version must be rolled out after 005; follow the migration README. The runtime still has no schema-owner or tenant-bypass privileges.

## Implemented state — release audit, 2026-11-13

The foundation descriptions below include historical planning. Current FastAPI modules implement auth, goals, onboarding, shared five-domain CRUD, bounded planning context, Gemini provider, chat and conversation storage. Migrations 001–004 define nine private tables. Runtime catalog inspection confirmed `momentum_app`, no superuser/BYPASSRLS, forced active RLS on all nine, and grants matching the migration README. There is no migration ledger, so table presence does not prove exact historical SQL execution or schema equivalence. No migration was rerun.

The frontend selects workspace views in React state; the active chat ID is in the URL. Assistant modes are loaded on demand. Later-phase code now includes approved memory, tutoring/interview sessions, action approvals, a Remotive cache and durable reminder/push workers; remote activation is unverified. Account export uses allowlisted bounded sections, verified-owner predicates and active RLS. Container/CI templates and a same-origin proxy are prepared, not deployed. See [release-plan.md](release-plan.md) for scope and gaps.

## Confirmed system direction

The intended system comprises a React + TypeScript + Vite frontend styled with Tailwind CSS, a Python + FastAPI backend, Neon PostgreSQL with Neon Auth, REST communication, and a hosted AI model accessed through a replaceable provider interface. It is intended for online deployment from the start.

## Repository layout (ADR-009)

Use the existing GitHub repository `Sammycode332/momentum-ai` as a monorepo with this intended layout.

- `frontend/` contains the React + TypeScript + Vite application styled with Tailwind CSS.
- `backend/` contains the Python + FastAPI application.
- `.agent/` contains engineering documentation.
- Root `AGENTS.md` coordinates agent work across the repository.

The minimum bootstrap is defined by ADR-010. `frontend/` will use the standard React + TypeScript + Vite scaffold, Tailwind CSS v4 through its Vite integration, npm, and a frontend-local `package-lock.json`. `backend/` will use a standard `pyproject.toml`, a virtual environment with pip, Uvicorn for local development, and a minimal `app/main.py` FastAPI application. Dependencies and configuration remain local to their respective applications; no root task runner or monorepo tooling is selected.

## Responsibilities and communication

`React client → authenticated REST API → FastAPI domain services → Neon PostgreSQL` is the intended primary path. The client obtains user authentication through Neon Auth and sends the resulting bearer token to the API. The API verifies the token against Neon Auth’s JWKS, pins its issuer, derives identity server-side, validates input, authorizes the operation, and invokes domain services. User-owned database rows are also protected by RLS.

The backend owns business rules, authorization, AI orchestration, memory proposal lifecycle, and permission enforcement. The frontend owns interaction and presentation only; it may not make trust decisions about user ownership.

## Frontend

Use React + TypeScript + Vite in `frontend/`, with Tailwind CSS v4 through its Vite integration for styling. npm and a frontend-local `package-lock.json` manage frontend dependencies. The minimum scaffold includes no UI component library. Routing, state management, data fetching, and component conventions remain unchosen. Organize UI, API client code, and domain-specific views so presentation does not become the authorization or business-rule layer.

## Backend

Use FastAPI in `backend/`. The minimum bootstrap uses a standard `backend/pyproject.toml`, a Python virtual environment with pip, Uvicorn for local development, and `backend/app/main.py` as the minimal application module. Route handlers should authenticate and validate requests, then delegate domain actions to focused services. Provider adapters should isolate Neon and hosted-AI SDK details. No custom application HTTP endpoint, including `/health`, is part of the bootstrap; FastAPI's framework-generated documentation and OpenAPI routes may remain enabled. The internal backend layout beyond the minimal module, validation library choices beyond FastAPI’s normal facilities, test framework, background-job strategy, and deployment topology are unresolved.

## Data and isolation

Neon PostgreSQL is the system of record. Expected user-owned domains include profile/onboarding context, projects, tasks, learning goals/progress, academic activities, opportunities, AI memory, memory proposals, and agent action/audit records. Specific tables, schemas, and relationships are not yet designed.

Under ADR-014, synchronous backend services can use `app.database.database_connection()` to open a transaction on demand and release the connection when the operation ends. Database access uses a backend-only `DATABASE_URL` with TLS and required SCRAM channel binding. The connection check is a backend command that runs `SELECT 1`. FastAPI startup and the existing authentication probe remain independent of database availability.

Every private record must be scoped to an authenticated owner and protected by RLS plus server-side authorization. Ownership is derived from verified identity; never accepted from the client as authority. Cross-user access is denied by default.

Privileged database credentials are not evidence of authorization. They may exist only in trusted backend runtime and never in browser code. Before a privileged query or mutation, the backend must verify the caller’s identity, authorize the requested action, and apply explicit ownership filtering. Prefer user-scoped database access subject to RLS where practical. Views, RPCs, privileged functions, and administrative access paths require security review because they can alter or bypass the intended policy boundary.

## Authentication and authorization flow

1. The frontend authenticates a user with Neon Auth.
2. For private API requests, it submits the authenticated credential using the agreed transport.
3. FastAPI verifies the bearer JWT with Neon Auth’s configured JWKS, issuer, expiration, subject, and supported signing algorithm; it then derives the principal, validates input, and authorizes the requested resource/action.
4. User-scoped database access runs with policies that prevent cross-user reads or writes. A privileged path instead applies explicit backend authorization and owner filtering, because it may bypass RLS.
5. The API returns only data authorized for that principal.

Neon Auth JWT verification is defined by ADR-013. The PostgreSQL connection foundation is available for later services. Applying verified user identity to database operations and testing RLS remain part of ID-02.

## AI, memory, and autonomy

Domain services assemble only the minimum authorized user context needed for a request, call an AI-provider interface, validate structured outputs, and return recommendations or proposed changes. Provider implementations must be replaceable.

Persistent AI memory changes follow a proposal → user review/approval → applied/audited lifecycle. Routine reprioritization or rescheduling may occur only after permissions, allowed actions, failure behavior, and audit/recovery rules are explicitly defined. The agent may not silently expand its authority.

## Deployment and integrations

Online deployment is required from the beginning. The MVP needs a minimal online deployment baseline: separated configuration, secret handling, an accessible frontend/backend path, and a documented migration/deployment procedure. Neon PostgreSQL and Neon Auth are the confirmed database/authentication service. Provider choices for frontend/backend hosting, AI, observability, secrets, scheduler/background execution, environments, and cost limits remain unresolved. Production hardening and release operations—monitoring, incident handling, rollback rehearsal, cost controls, and operational validation—are later release-readiness work. Do not assume free tiers meet requirements.
