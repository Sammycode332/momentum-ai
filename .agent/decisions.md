# Architecture Decision Records

Use a new dated ADR for every material architecture choice. Do not change an ADR to hide history; supersede it with a later ADR.

## ADR-001 — Core technology direction

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** Momentum AI needs a browser client, secure backend, hosted authentication/database, REST API, and AI capability.
- **Decision:** Use React + TypeScript for the frontend, Python + FastAPI for the backend, Supabase PostgreSQL and Supabase Auth, REST between frontend/backend, and a hosted AI provider behind a replaceable interface.
- **Alternatives considered:** Other technology stacks and direct vendor-specific AI coupling.
- **Reasoning and trade-offs:** This is the supplied project direction. It retains flexibility in framework and AI provider selection but requires clear boundary interfaces and later operational decisions.

## ADR-002 — React framework selection

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** Momentum AI has a separate FastAPI backend and does not require server-side rendering. The frontend needs an interactive authenticated dashboard and direct REST communication with FastAPI.
- **Decision:** Use React + TypeScript + Vite for the frontend.
- **Alternatives considered:** Next.js with a separate FastAPI backend; other React-compatible approaches.
- **Reasoning and trade-offs:** Vite keeps the browser frontend and FastAPI backend boundary clear, avoids adding a second server-side application layer, and supports the interactive dashboard. This decision does not select repository layout, routing, hosting, or a server-rendering strategy.

## ADR-003 — Tenant protection in depth

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** Private multi-user records and AI context require strong isolation.
- **Decision:** Enforce private-resource access server-side and with PostgreSQL RLS; derive identity from verified authentication and never rely on frontend filters.
- **Alternatives considered:** Frontend-only filtering; backend checks without RLS.
- **Reasoning and trade-offs:** Defense in depth reduces cross-tenant exposure risk; it requires RLS policy tests and disciplined data access.

## ADR-004 — AI provider abstraction

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** A hosted provider is required but vendor is undecided.
- **Decision:** Access hosted models through a replaceable backend provider interface.
- **Alternatives considered:** Calling a vendor SDK throughout domain code.
- **Reasoning and trade-offs:** Preserves provider portability and testability at the cost of a small adapter boundary.

## ADR-005 — Memory approval lifecycle

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** Users must review and approve proposed memory updates.
- **Decision:** Persist AI memory changes only through an explicit proposal/review/approval lifecycle with auditability.
- **Alternatives considered:** Immediate automatic writes; no persistent structured memory.
- **Reasoning and trade-offs:** User control and integrity outweigh friction; exact schema and review UI remain to be designed.

## ADR-006 — Hosting and operations baseline

- **Date:** 2026-11-12
- **Status:** proposed
- **Context:** Online deployment is required, but hosting, environments, migrations, monitoring, cost limits, and scheduling are unselected.
- **Decision:** Establish a provider-agnostic minimal online MVP deployment baseline before MVP delivery, then decide production-hardening and release operations before production release; do not represent any provider or free-tier assumption as agreed.
- **Alternatives considered:** Choosing a host/scheduler now.
- **Reasoning and trade-offs:** Preserves the requirement for online MVP deployment without prematurely selecting providers. It defers production-hardening commitments until MVP needs and costs are clear.

## ADR-007 — API versioning and error conventions

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** Private API endpoints need a stable path and safe, predictable failure responses before implementation. The bootstrap intentionally introduced no custom endpoints, middleware, or exception handlers.
- **Decision:** Private application API endpoints use the `/api/v1/...` path prefix. HTTP status codes retain their standard meanings. Application-generated error responses use `{"error":{"code":"MACHINE_READABLE_CODE","message":"Safe human-readable message"}}`; an optional `details` member may include only safe validation information. Authentication failures use `401 Unauthorized`; authenticated callers without permission use `403 Forbidden`. Error responses must not expose stack traces, credentials, internal database details, or sensitive user information. FastAPI's framework-generated `/docs` and `/openapi.json` routes remain unchanged.
- **Alternatives considered:** Unversioned private endpoints; framework-default or endpoint-specific error shapes; changing the framework-generated documentation/OpenAPI routes; adopting middleware or exception handlers before private endpoints exist.
- **Reasoning and trade-offs:** A versioned prefix and uniform application error envelope give clients a stable, safe contract while retaining normal HTTP semantics. Deferring runtime enforcement avoids adding unused code or dependencies; each future endpoint and handler must implement and test this contract without leaking sensitive information.

## ADR-008 — Frontend styling

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** The selected React + TypeScript + Vite frontend needs a consistent styling approach without committing to a UI component library.
- **Decision:** Use Tailwind CSS for frontend styling.
- **Alternatives considered:** CSS modules, styled components, another utility-first CSS system, and a preselected UI component library.
- **Reasoning and trade-offs:** Tailwind CSS provides a shared utility-based styling convention while keeping the UI component-library choice open. This decision does not select a Tailwind version, design system, component library, or repository structure.

## ADR-009 — Monorepo layout

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** Momentum AI has distinct frontend and backend stacks with shared engineering documentation. The project owner approved a single repository for both applications and their documentation.
- **Decision:** Use the existing GitHub repository `Sammycode332/momentum-ai` as a monorepo. Place React + TypeScript + Vite + Tailwind CSS in `frontend/`, Python + FastAPI in `backend/`, engineering documentation in `.agent/`, and agent coordination in root `AGENTS.md`.
- **Alternatives:** Separate repositories for the frontend and backend, or a single repository with application files at the root.
- **Reasoning and trade-offs:** One repository lets related UI, API, and documentation changes be reviewed together. Top-level application directories keep the two stacks distinct. A shared repository requires care to scope tooling and checks to the relevant application. Bootstrap details and deployment topology remain open.

## ADR-010 — Minimum local application bootstrap

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** FND-01 requires a reproducible minimum bootstrap for both applications in the accepted monorepo. The project needs local development and verification commands without prematurely selecting API conventions, test tooling, deployment tooling, or application architecture.
- **Decision:** FND-01 includes both application roots. `frontend/` will use the standard React + TypeScript + Vite scaffold, Tailwind CSS v4 through its Vite integration, npm, and a frontend-local `package-lock.json`; it will not add a UI component library. `backend/` will use FastAPI with a standard `pyproject.toml`, Python virtual environment and pip, Uvicorn for local development, and a minimal `app/main.py` application. Dependencies and configuration remain scoped to each application. No pnpm workspaces, Turborepo, Nx, Docker, Poetry, uv, or root task runner are selected at this checkpoint. The bootstrap introduces no custom HTTP endpoints, including `/health`; FastAPI-generated documentation and OpenAPI routes may remain enabled.
- **Alternatives considered:** A frontend-only bootstrap; root-level monorepo tooling; Docker; Poetry or uv; a backend test framework; a custom health endpoint.
- **Reasoning and trade-offs:** Per-application native tooling keeps the first increment small, inspectable, and consistent with the accepted monorepo boundary. It gives both stacks a local run path while avoiding new orchestration, deployment, API-contract, or testing commitments. This intentionally defers a backend test framework to FND-03 and custom endpoints until FND-05 records API versioning and error conventions.

## ADR-011 — Public and server-only configuration boundary

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** FND-02 requires a local/staging configuration approach and protections against accidentally committing secrets. The Vite frontend and FastAPI backend have different exposure boundaries, while hosting, providers, and runtime configuration libraries remain unselected.
- **Decision:** Ignore `.env` and `.env.*` repository-wide while allowing value-free `.env.example` templates. Local configuration may use ignored environment files or process environment variables; staging and production configuration is injected by the eventual hosting environment. Treat every Vite `VITE_*` value as public browser configuration. Keep privileged credentials, including Supabase `service_role`, AI API keys, database credentials, and signing secrets exclusively in backend runtime configuration. A Supabase URL and publishable/anon key may be browser configuration only after the relevant access path is protected and verified; it is not an authorization control.
- **Alternatives considered:** App-specific ignore rules only; committing environment-specific configuration; exposing privileged credentials through browser configuration; selecting dotenv, a settings library, a secret manager, a hosting platform, or provider configuration now.
- **Reasoning and trade-offs:** A repository-wide rule closes the current frontend `.env` gap and makes the convention consistent across the monorepo. Explicit template exceptions support onboarding without committing values. Deferring configuration loaders and providers avoids unused dependencies and premature operational commitments, but future configuration-consuming features must add validation and an approved implementation.

## ADR-012 — Initial test tooling and controlled fixtures

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** FND-03 requires executable unit/integration test commands and a fixture policy that supports future tenant-isolation and privileged-access testing. The frontend and backend scaffolds have no test framework.
- **Decision:** Use Vitest, jsdom, React Testing Library, and @testing-library/jest-dom for frontend tests. Use pytest, httpx, and FastAPI's synchronous TestClient for backend tests. Keep dependencies local to their applications. Start with deterministic smoke tests and synthetic user_a, user_b, and privileged_actor fixtures; they are not credentials or real service accounts. Do not add browser automation, external databases, mocking frameworks, or async-test plugins at this checkpoint.
- **Alternatives considered:** Deferring executable tests; a root test runner; browser automation; unittest-only backend tests; external database fixtures; broad mocking or async test tooling.
- **Reasoning and trade-offs:** The selected tools integrate with the accepted Vite/React and FastAPI stacks and enable component and route verification with a small dependency footprint. Synthetic fixtures establish the tenant-testing shape before services exist, but they cannot replace later Supabase/RLS and privileged-path integration tests.
