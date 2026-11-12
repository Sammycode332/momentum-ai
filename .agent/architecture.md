# Technical Architecture

## Confirmed system direction

The intended system comprises a React + TypeScript frontend, a Python + FastAPI backend, Supabase PostgreSQL with Supabase Auth, REST communication, and a hosted AI model accessed through a replaceable provider interface. It is intended for online deployment from the start. No source implementation exists yet.

## Responsibilities and communication

`React client → authenticated REST API → FastAPI domain services → Supabase PostgreSQL` is the intended primary path. The client obtains user authentication through Supabase Auth and sends the resulting credential to the API. The API verifies the credential, derives identity server-side, validates input, authorizes the operation, and invokes domain services. User-owned database rows are also protected by RLS.

The backend owns business rules, authorization, AI orchestration, memory proposal lifecycle, and permission enforcement. The frontend owns interaction and presentation only; it may not make trust decisions about user ownership.

## Frontend (confirmed direction; structure proposed)

Use React + TypeScript. The exact React framework, routing, rendering, state-management, data-fetching, and component conventions are unchosen. When selected, organize UI, API client code, and domain-specific views so presentation does not become the authorization or business-rule layer.

## Backend (confirmed direction; structure proposed)

Use FastAPI. Route handlers should authenticate and validate requests, then delegate domain actions to focused services. Provider adapters should isolate Supabase and hosted-AI SDK details. The exact project layout, validation library choices beyond FastAPI’s normal facilities, background-job strategy, and deployment topology are unresolved.

## Data and isolation

Supabase PostgreSQL is the system of record. Expected user-owned domains include profile/onboarding context, projects, tasks, learning goals/progress, academic activities, opportunities, AI memory, memory proposals, and agent action/audit records. Specific tables, schemas, and relationships are not yet designed.

Every private record must be scoped to an authenticated owner and protected by RLS plus server-side authorization. Ownership is derived from verified identity; never accepted from the client as authority. Cross-user access is denied by default.

Supabase `service_role` credentials bypass RLS and are therefore not evidence of authorization. They may exist only in trusted backend runtime and never in browser code. Before a privileged query or mutation, the backend must verify the caller’s identity, authorize the requested action, and apply explicit ownership filtering. Prefer user-scoped database access subject to RLS where practical. Views, RPCs, privileged functions, and administrative access paths require security review because they can alter or bypass the intended policy boundary.

## Authentication and authorization flow

1. The frontend authenticates a user with Supabase Auth.
2. For private API requests, it submits the authenticated credential using the agreed transport.
3. FastAPI verifies it with the selected supported mechanism, derives the principal, validates input, and authorizes the requested resource/action.
4. User-scoped database access runs with policies that prevent cross-user reads or writes. A service-role path instead applies explicit backend authorization and owner filtering, because it bypasses RLS.
5. The API returns only data authorized for that principal.

Exact token-verification configuration and how FastAPI accesses Supabase are proposed decisions, not implemented facts.

## AI, memory, and autonomy

Domain services assemble only the minimum authorized user context needed for a request, call an AI-provider interface, validate structured outputs, and return recommendations or proposed changes. Provider implementations must be replaceable.

Persistent AI memory changes follow a proposal → user review/approval → applied/audited lifecycle. Routine reprioritization or rescheduling may occur only after permissions, allowed actions, failure behavior, and audit/recovery rules are explicitly defined. The agent may not silently expand its authority.

## Deployment and integrations

Online deployment is required from the beginning. The MVP needs a minimal online deployment baseline: separated configuration, secret handling, an accessible frontend/backend path, and a documented migration/deployment procedure. Supabase is the confirmed authentication/database service. Provider choices for frontend/backend hosting, AI, observability, secrets, scheduler/background execution, environments, and cost limits remain unresolved. Production hardening and release operations—monitoring, incident handling, rollback rehearsal, cost controls, and operational validation—are later release-readiness work. Do not assume free tiers meet requirements.
