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
- **Status:** proposed
- **Context:** React + TypeScript is confirmed, but no frontend framework is selected.
- **Decision:** Select a React framework only after evaluating deployment needs, authentication integration, routing/rendering needs, team familiarity, and 10-hour MVP impact.
- **Alternatives considered:** Next.js; a client-rendered React setup; other React-compatible approaches.
- **Reasoning and trade-offs:** Next.js is possible, not agreed. Premature selection risks unnecessary architecture and dependency commitment.

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
- **Decision:** Decide these before production deployment; do not represent any provider or free-tier assumption as agreed.
- **Alternatives considered:** Choosing a host/scheduler now.
- **Reasoning and trade-offs:** Defers infrastructure commitment until MVP needs and costs are clear, while blocking production release planning.
