# Product Specification

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

The initial build target is about 10 hours. MVP means a thin, validated vertical slice of the journeys above, not exhaustive workflow coverage or autonomous background operation. Scope changes require an explicit trade-off recorded in the roadmap and tasks.

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
