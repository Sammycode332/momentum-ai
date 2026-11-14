# Product Specification

The [master specification](master-specification.md) is the authoritative release
scope. It preserves all 22 sections and Phases 0–9. This file records the earlier
MVP context. A five-phase progress summary is a reporting view only. Use the
[coverage and roadmap audit](scope-audit.md) for current evidence and gaps.

## Release mission scope update — 2026-11-13

The owner's master completion mission expands the earlier MVP to tutoring, interviews, verified opportunity discovery, durable notifications/PWA, approved memory, controlled actions, and commercial release preparation. The older exclusions below describe the original MVP, not a prohibition on the expanded mission. Acceptance gates and actual feature status are tracked in [release-plan.md](release-plan.md). No provider costs or production changes are implicitly approved.

## Confirmed product vision

Momentum AI is a multi-user personal AI growth and execution assistant for students, developers, and professionals. It combines projects, technical development, learning, academics, career goals/opportunities, tasks, priorities, and commitments so an assistant can recommend realistic next actions and help maintain progress.

The product must provide independent accounts, dashboards, records, and AI memory. A user must never be able to access another user’s private information.

## Problem and users

People balancing several growth domains lack a single context-aware system to decide what is most valuable and achievable next. Momentum AI must make cross-domain, evidence-based recommendations rather than merely list tasks or provide generic encouragement.

Primary users: students, developers, and professionals with overlapping project, learning, academic, career, and personal commitments.

## Confirmed MVP journeys and requirements

1. **Account and onboarding:** a user registers, authenticates, and completes a short guided onboarding that records enough circumstances and goals to personalize the product.
2. **Personalized dashboard:** authenticated users see their own prioritized snapshot, plans, relevant records, and recommended next actions.
3. **Core records:** users can manage projects, tasks, learning/skill goals, academic activities/deadlines, and career opportunities relevant to their own goals.
4. **AI planning:** the assistant uses saved, authorized user context to offer realistic, evidence-based plans and recommendations across domains.
5. **Structured memory:** the assistant proposes memory changes; the user can review and approve them before they become persistent memory.
6. **Controlled autonomy:** within explicitly defined permissions, the system may reprioritize and reschedule routine tasks. It must remain bounded, auditable, and recoverable.
7. **Multi-user privacy:** all records, dashboards, context, memory, and agent actions are isolated by user.

## MVP boundaries

The MVP deliberately retains all five core record domains and the full set of confirmed journeys above. It is broader than the original approximate 10-hour estimate; no completion-time promise is currently made. It remains a validated first release rather than exhaustive workflow coverage, unsupervised background operation, or broad automation. Scope changes require an explicit trade-off recorded in the roadmap and tasks.

## Explicitly excluded from MVP

- Background monitoring or unsupervised long-running agents.
- Automated internship or job discovery.
- GitHub integration.
- Advanced analytics.
- Additional notification channels.
- Broad automation beyond controlled routine task reprioritization/rescheduling.

## Proposed future capabilities (not requirements)

The excluded features above may be considered after the MVP. More complex planning, integrations, analytics, and notifications must be designed from observed needs and evaluated for privacy, cost, and reliability before commitment.

## Open product detail

The exact onboarding questions, dashboard composition, task autonomy permission model, retention policy, AI provider, and acceptance metrics require confirmation; see `decisions.md` and `blockers.md`.
