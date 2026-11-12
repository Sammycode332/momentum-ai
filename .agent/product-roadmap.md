# Product Roadmap

## MVP

The MVP is a secure, broader first release. It deliberately retains the following complete scope and does not promise a completion time:

- Multi-user authentication.
- Short guided onboarding.
- Personalized dashboards.
- User-specific core records.
- Core AI planning.
- Structured memory proposals and user approval.
- Controlled routine task reprioritization and rescheduling, with approval gates for consequential changes.
- Core evaluation tests, including safety and tenant isolation.

The delivery sequence is foundation (including the minimal online deployment baseline) → authentication/RLS → onboarding/core records → dashboard → AI planning/memory → controlled autonomy → evaluations → validated MVP deployment → production-hardening/release checks. Each addition must preserve user isolation and have evidence-based acceptance criteria. Online MVP deployment is required from the beginning; production hardening and release operations are separate later work.

## Stretch / post-MVP

- Background monitoring.
- Automated internship and job discovery.
- GitHub integration.
- Advanced analytics.
- Additional notification channels.

## Scope governance

Do not add an MVP capability without documenting what is deferred and the security/cost impact, plus any new decision or blocker. Provider selections, background scheduling, integrations, and sophisticated automation are not implicitly in scope merely because they may be useful later. Online MVP deployment is required, but it must not silently select a hosting provider or substitute for production-hardening work.
