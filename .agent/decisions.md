# Architecture Decision Records

## ADR-025 — Feature completion boundaries (2026-11-13)

- Extend the existing PostgreSQL/RLS and Gemini adapter; no replacement stack. New migrations are additive and remain separate from applied 001–004. A shared owner-scoped cursor verifies active RLS before setting transaction-local identity; all services also filter by owner.
- Memory remains pending until explicit approval. Corrections reset approval. Audit only action/target/time, not memory text. Personalization can be disabled. Retrieve at most five approved memories by lexical relevance; explicit user instructions take precedence.
- Tutoring and interview sessions persist structured curriculum/questions, user answers and bounded AI feedback. A lesson is not mastered by viewing it. Rubric scores are formative model judgments, not hiring predictions. A submitted answer is evaluated once per step via an idempotent request ID and row lock.
- AI actions are typed proposals; execution requires an explicit authenticated approve request, a pending row lock, normal ownership checks and one transaction with audit. No automatic execution or SQL tools.
- Durable reminders use PostgreSQL scheduling state and a separate worker process, with a separate least-privilege scheduler role. No browser timer is the delivery mechanism. External push requires configured VAPID keys and supported devices; no paid service is selected.
- Live discovery will use authorized sources only and expose source limitations. Unsupported categories must show no-provider information, not generated listings. Provider credentials/costs, production rollout and schema-owner activation remain external gates.

## ADR-024 — Goal lifecycle (2026-11-13)

- Extend personal goals with a `completed` boolean, initially false. Completion is a user assertion, not AI-assessed mastery. Use authenticated PATCH for title/completion and DELETE for explicit removal. Partial updates prevent toggling completion from overwriting the title.
- Migration 005 adds the column, owner-only UPDATE/DELETE RLS and narrowly scoped runtime UPDATE(title, completed)/DELETE grants. Keep migrations 001–004 unchanged. Apply 005 before enabling the new backend version; rollback the app while retaining the column and data.
- All queries retain explicit verified-owner filters and the active-RLS check. Missing/foreign IDs return the same 404. No new dependency or background task is needed.
- At the owner's direction, later-phase implementation may proceed with the first-load authentication blocker deferred; this does not waive authentication or release verification gates.

## ADR-023 — Release reliability increment (2026-11-13)

- Keep the existing stack and strict JWT validation. Distinguish future-issued/not-before token rejection with `ACCESS_TOKEN_NOT_YET_VALID`; log only request reference and error class. This is diagnostic coverage, not a verified fix for the reported intermittent failure. No clock leeway, delays or request replay are introduced.
- Limit new/updated core record descriptions to 4,000 characters and reject NUL in all record input strings before PostgreSQL. Existing stored records are not rewritten. This API boundary does not replace deployment request-body and rate limits.
- Load the assistant via React lazy/Suspense to avoid loading Markdown and planning UI on Overview. Keep an accessible loading state.
- Allow the development Vite proxy target to be set through server-side `MOMENTUM_DEV_API_TARGET` for isolated diagnosis; default stays port 8001. This is not a production proxy/CORS design.

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
- **Reasoning and trade-offs:** The selected tools integrate with the accepted Vite/React and FastAPI stacks and enable component and route verification with a small dependency footprint. Synthetic fixtures establish the tenant-testing shape before services exist, but they cannot replace later Neon RLS and privileged-path integration tests.

## ADR-013 — Neon PostgreSQL and Neon Auth migration

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** The project owner selected Neon PostgreSQL and Neon Auth (Managed Better Auth) for the first working authentication milestone, replacing the Supabase PostgreSQL and Auth direction in ADR-001. The application remains a React/Vite browser client with a FastAPI backend and REST boundary.
- **Decision:** Use Neon PostgreSQL as the system of record and Neon Auth for managed email/password authentication. The browser uses the official @neondatabase/auth React adapter against a public Neon Auth URL. FastAPI verifies bearer JWTs using NEON_AUTH_JWKS_URL and pins the issuer derived from NEON_AUTH_BASE_URL. The current Neon branch publishes EdDSA signing keys; the backend accepts EdDSA only. No audience is enforced unless Neon’s token contract for a future protected resource requires one. The backend derives the subject only from a verified token and uses the ADR-007 error envelope for auth failures.
- **Alternatives considered:** Retaining the unimplemented Supabase plan; direct Better Auth client usage; a custom password database or authentication server; accepting unverified browser session data; accepting arbitrary JWT algorithms.
- **Reasoning and trade-offs:** Neon Auth provides managed Better Auth sessions and branch-scoped JWKS while keeping identity data with Neon PostgreSQL. Pinning issuer, JWKS, required time claims, subject, and the published algorithm gives FastAPI a narrow verification boundary. The change requires provider-specific configuration and later Neon RLS/data-isolation verification; it does not choose an ORM, database migration tool, host, or service credentials.

## ADR-014 — Backend PostgreSQL connection foundation

- **Date:** 2026-11-12
- **Status:** accepted for the database foundation checkpoint
- **Context:** ID-02 needs a backend connection to the Neon development database and a read-only connectivity check before implementing schemas and RLS.
- **Decision:** Use synchronous Psycopg 3 for context-managed connections opened on demand in backend services. Use a backend-only `DATABASE_URL` with a least-privileged development role. Enforce TLS and SCRAM channel binding as documented by [Neon](https://neon.com/blog/postgres-needs-better-connection-security-defaults). Use an operator-run `SELECT 1` smoke check. Future synchronous callers can use Neon's pooled endpoint for application traffic if needed.
- **Reasoning and trade-offs:** Per-operation connections bound transaction and connection lifetimes and keep database availability out of FastAPI startup. Opening a connection adds latency. Defer an in-process pool, SQLAlchemy, and Alembic until the application has data workloads or migrations to justify them. Database login identifies a database role. Ownership and tenant isolation still require verified Neon Auth identity, explicit authorization, and RLS under ADR-003.

## ADR-015 — Personal Goals schema and ownership

- **Date:** 2026-11-12
- **Status:** accepted for the Personal Goals checkpoint
- **Decision:** Use a numbered, transactional SQL migration applied by an operator. Store the verified Neon Auth subject as the owner. Set that subject as transaction-local PostgreSQL context, filter reads and scope writes explicitly in the backend, and require active RLS for the connection's database role. The API accepts only a title when creating a goal.
- **Trade-offs:** This first migration needs no ORM or migration dependency. The database trusts the backend to set the subject, so database credentials stay backend-only. Use a non-owner runtime role with SELECT and INSERT for deployment, and keep migration credentials separate. Reassess tooling when migrations need automated ordering or deployment tracking.

## ADR-016 — User onboarding preferences

- **Date:** 2026-11-13
- **Status:** accepted
- **Decision:** Collect primary focus, current goals as free text, and preferred daily planning time as a local HH:MM preference. Allow a persistent skip and later edits. Store one row per verified Neon Auth subject, with the same transaction-local identity and forced RLS pattern as Goals. The onboarding goals summary is separate from Personal Goals records.

## ADR-017 — Core records schema and API

- **Date:** 2026-11-13
- **Status:** accepted for CORE-01
- **Decision:** Add five owner-scoped tables through one transactional migration and expose consistent authenticated CRUD routes at `/api/v1/{projects,tasks,learning,academics,opportunities}`. Every table uses forced RLS and owner policies for all CRUD operations. Tasks reference projects through a composite `(project_id, owner_id)` foreign key, and the API validates that a selected project belongs to the verified caller.
- **Trade-offs:** A small shared route implementation keeps equivalent domain behavior consistent without introducing an ORM. It intentionally does not provide planning or dashboard prioritization, which remain CORE-02 work.

## ADR-018 — Dashboard composition

- **Date:** 2026-11-13
- **Decision:** Derive the dashboard in the browser from the five existing authenticated record lists. Fetch onboarding separately for optional primary-focus personalization. Keep the backend as the authorization boundary and reuse the existing task and project creation forms.
- **Dashboard rules:** Active means not started or in progress. Outstanding tasks include all incomplete tasks. Today’s priorities include incomplete tasks due today or overdue, sorted by due date and then priority. Upcoming deadlines include incomplete tasks, academic activities, and opportunities dated today through six days ahead in the browser’s local calendar.

## ADR-019 — Read-only Gemini planning

- **Date:** 2026-11-13
- **Decision:** Use the Google Gen AI SDK behind a replaceable provider interface. The backend uses verified identity and existing RLS connections to select bounded context. Request-local aliases identify task and project references sent to Gemini. Validate output shape, time budget, and reference membership before returning the plan.
- **Release boundary:** Enable live use only with a Gemini configuration approved for the data being sent. Keep plans in component state and provide no tools, record mutations, or memory persistence.

## ADR-020 — Conversational assistant

- **Decision:** Add authenticated `POST /api/v1/ai/chat` with bounded explicit user/assistant history and validated replies. Reuse the Gemini adapter and owner-scoped planning context. Keep the structured planner available separately. Keep chat history in page memory and send only recent turns; no history table is required.
- **Configuration:** Read nonblank process values first and use the backend-local dotenv file for missing values. Require both the API key and an explicit model. Keep provider settings server-side.

## Protected request token freshness

- Reuse the Neon session adapter. If its cached token is opaque, expired, or within 15 seconds of expiry, coalesce one uncached Neon session fetch before dispatching private requests. This margin covers request transit and clock skew. FastAPI remains responsible for signature and claim verification. API responses are never replayed automatically.

## ADR-021 — Assistant Markdown and streaming boundary

- Render assistant text with react-markdown and an allowlist of formatting elements. Disable raw HTML, links, and images. Keep user messages as plain text.
- Keep chat replies atomic and schema-validated. Defer streaming until the transport can distinguish incomplete output from a committed reply, propagate cancellation, and preserve history across interruptions.

## ADR-022 — Persistent conversation history

- Chat task creation uses the existing action store. A deterministic ID derived from the verified owner, conversation, and turn links the proposal to chat without a schema change. Persist the proposal, audit event, and assistant turn in one transaction. Only committed approval responses supply execution status. Task deadlines remain date-only.
- Explicit questions about the caller's workspace use bounded, owner-scoped SQL and server-rendered summaries. They do not send records to the AI provider or depend on background personalization preferences. Today and the next seven calendar days use the browser timezone. Goal progress reports linked task completion separately from the goal's saved completion flag.
- Conversational task edits propose one field at a time. The model extracts a search phrase and requested value. The backend resolves the phrase using owner-scoped search, records the old value and task version, and locks and rechecks the same task before applying the approved patch.
- Milestone C stores goal description and target date in the action history because the Goals schema has title and completion only. Roadmap approval saves the goal and selected phases atomically. Each phase creates one project, one milestone task and its subtasks. Tasks link to the goal and project, and subtasks also link to the milestone. Sequence and workload estimates remain review metadata. Persist the execution receipt in the existing action JSON so approval retries can return the original record IDs.

- Keep conversations and ordered messages in owner-scoped PostgreSQL tables. The client supplies an opaque turn ID for retry deduplication. Save the user turn before generation and append the assistant turn only after validation. Serialize generation for each conversation using a nonblocking row lock. A failed user turn can be retried with the same ID.
- Keep only the active conversation ID in the URL. Fetch bounded recent history for display and send up to nine recent messages within the existing character budget to Gemini. Conversation history does not write to approved memory.


## ADR-026 — Consolidated assistant and navigation

2026-11-13, explicit owner direction: prioritize frontend and remove redundant standalone tutoring/interview navigation. AI Assistant offers Chat, Learn, Interview and Approvals modes. Guided practice retains its private session API and history; modes are not separate primary destinations. Keep visited modes mounted to preserve drafts and in-flight work while switching. Learning remains saved activities; opportunity discovery lives beside saved opportunities; approved memory is under Settings. No new UI dependency.

## ADR-027 — Bounded account export and deployment baseline

Authenticated users can export allowlisted workspace sections in stable, bounded pages. Never export push subscription endpoints/keys, provider secrets, bearer tokens or another owner. Every query requires active RLS and an explicit verified-owner predicate. A multi-page export is not a transactionally frozen snapshot; the download records this limitation. Do not label workspace clearing as Neon identity deletion. Full account erasure remains gated on provider identity deletion and an agreed audit/backup retention procedure.

Prepare container/CI templates and a same-origin reverse proxy without choosing a paid host or deploying. Production TLS terminates at the chosen hosting ingress; backend stays private. A separate supervised scheduler runs the worker. Public liveness reports process health only; authenticated readiness checks are operational, not proof of full release readiness.

## ADR-028 — Provider-managed account recovery

Use the installed Neon SDK requestPasswordReset/resetPassword methods rather than custom recovery tokens. The return address is fixed to the current origin with flow=reset-password. Strip token/error query values when the recovery component mounts; retain the token only in memory. Request messaging does not confirm account existence. Google OAuth UI is gated behind an explicit public configuration flag, default false, until provider setup is verified. No provider credentials are generated or changed by this implementation.

## ADR-029 — Connected productivity workflows

Add opportunity application_stage independently of general record status, default saved, preserving prior status/data. Record reminder actions open an explicit editable one-off reminder composer; they copy title/date and are not advertised as automatically synchronized links. Project task/milestone views derive progress from saved task completion only. Overview goals/reminders use separately recoverable authenticated reads so an unavailable optional section does not hide core records. Owner requested feature-first implementation; run build/import checks here and defer broad workflow suites until integration.

## ADR-030 — Check-in shortcuts and bounded inbox actions

Reuse daily reminders for optional morning/evening check-ins. Shortcut buttons populate an editable composer; they do not save or enable anything without submission. An existing same-title scheduled daily reminder is opened for editing. Bulk notification state changes accept at most 100 explicit IDs, always filter by verified owner and active RLS, and do not revive dismissed notifications. UI labels make clear that counts/actions concern loaded records, not an unbounded inbox. No additional migration or provider cost.

## ADR-031 — Safe reversal of approved deadline changes

Only reschedule_task actions support automatic undo. Approval writes task updated_at and action applied_at using PostgreSQL transaction time; undo requires both the applied deadline and that timestamp to match. Any later task update prevents undo. Restore only the previous deadline, never delete AI-created records. Lock the owned proposal and target, and record reverted state/audit in the same transaction. Retry of an already reverted action is a no-op. Reschedule proposal titles come from the owned database task rather than AI-supplied text. Migration 014 extends action state/history; no remote application assumed.
