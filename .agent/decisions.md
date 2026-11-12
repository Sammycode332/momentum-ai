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
- **Status:** proposed
- **Context:** Agents must not expose REST endpoints until API versioning and error conventions are agreed, but no convention has been selected.
- **Decision:** Define and record a minimal API versioning and error-response convention before the first private API endpoint is implemented.
- **Alternatives considered:** Unversioned endpoints; adopting a convention implicitly during implementation.
- **Reasoning and trade-offs:** This preserves client compatibility and predictable failures without choosing an API design prematurely.

## ADR-008 — Frontend styling

- **Date:** 2026-11-12
- **Status:** accepted
- **Context:** The selected React + TypeScript + Vite frontend needs a consistent styling approach without committing to a UI component library.
- **Decision:** Use Tailwind CSS for frontend styling.
- **Alternatives considered:** CSS modules, styled components, another utility-first CSS system, and a preselected UI component library.
- **Reasoning and trade-offs:** Tailwind CSS provides a shared utility-based styling convention while keeping the UI component-library choice open. This decision does not select a Tailwind version, design system, component library, or repository structure.
