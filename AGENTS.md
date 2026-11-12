# Momentum AI — Agent Operating Guide

## Project overview

Momentum AI is a multi-user personal AI growth and execution assistant. It connects a user’s projects, learning, academics, career opportunities, tasks, and commitments to help them decide and execute what matters next. It is not a generic task list or motivational chatbot.

The agreed technical direction is React + TypeScript on the frontend, Python + FastAPI on the backend, Supabase PostgreSQL and Auth, REST between frontend and backend, and a hosted AI provider behind a replaceable interface. No framework, host, scheduler, or provider has been selected beyond that direction.

## Required reading order

Before every task, read this file and `.agent/spec.md`. Then read only the documents applicable to the task:

1. `.agent/architecture.md` for system boundaries or implementation placement.
2. `.agent/security.md` for any authentication, authorization, data, API, integration, or logging work.
3. `.agent/decisions.md` before making a technology or architectural choice.
4. `.agent/tasks.md`, `.agent/progress.md`, and `.agent/blockers.md` to select and report work.
5. `.agent/testing.md` before writing or changing tests, AI behavior, or user-record mutations.
6. `.agent/product-roadmap.md` when assessing scope.

Inspect the repository before assuming a structure or changing code. Treat docs as current planning context; verify them against the code when implementation exists.

## Engineering rules

- Build small, testable increments. Complete one meaningful capability before expanding scope.
- Keep confirmed facts, assumptions, and proposals distinct. Do not invent requirements.
- Do not rewrite working code, duplicate existing functionality, add dependencies, or make major architectural changes unless the task requires it and the decision is recorded.
- Prefer clear, narrow interfaces and cohesive modules over speculative abstractions.
- Do not start a feature whose prerequisites or security model are unknown; record the blocker and request direction where needed.

## Before coding

- Read the required context and inspect relevant code, tests, configuration, migrations, and APIs.
- Locate the applicable task or add a narrowly scoped proposed task; check dependencies and blockers.
- State any meaningful assumptions. Record durable architecture choices in `decisions.md` before relying on them.
- Define acceptance criteria and a proportionate test plan.

## Conventions

### Frontend

- Use React + TypeScript. Do not assume Next.js or another React framework until an ADR accepts it.
- Keep presentation, client state, API access, and domain behavior separated as the selected framework permits.
- Treat backend authorization as authoritative; frontend visibility is never access control.
- Avoid storing secrets or privileged credentials in browser code.

### Backend and API

- Use Python + FastAPI. Keep route handling thin; place domain logic, validation, authorization, and provider adapters in appropriate layers.
- Expose versioned REST endpoints only after API versioning and error conventions are agreed.
- Validate input and authenticate every private request. Resolve identity server-side and authorize the requested resource before reading or mutating it.
- Keep AI providers behind an interface; application domain code must not depend directly on one vendor SDK.

### Database

- Use Supabase PostgreSQL. Every user-owned row must carry an owner identity and be protected with PostgreSQL Row Level Security (RLS).
- Use reviewed, reversible migration practices after the migration tool is selected. Never modify production data manually without an approved operational procedure.
- Design indexes and constraints from actual access patterns; preserve auditability for memory approvals and autonomous changes.

## Authentication, authorization, and security

- Supabase Auth authenticates users; backend services must verify tokens and enforce authorization for every private resource.
- Enforce tenant boundaries both in backend logic and database RLS. Never trust client-supplied user IDs or frontend filtering.
- Keep secrets in environment-managed configuration, never source control, UI bundles, logs, prompts, or error messages.
- Treat AI memory, prompts, recommendation inputs, and AI-provider outputs as sensitive user data. Follow `.agent/security.md`.

## Testing and completion

- Test behavior, failures, and relevant edge cases—not only compilation. Prioritize auth, RLS/data isolation, memory integrity, and agent permissions.
- Use controlled fixtures or test copies for tests that mutate records.
- Run relevant checks and report the commands/results or explain why verification could not run.
- Update `tasks.md`, `progress.md`, `blockers.md`, and decisions/testing docs when work changes their truth. Never mark work complete without evidence.

## Required task completion report

Every implementation task report must state: changed files and behavior; tests run and results; security/privacy implications; decisions or assumptions recorded; documentation updates; known limitations/blockers; and the recommended next task.
