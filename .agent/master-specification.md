# MOMENTUM AI — MASTER PRODUCT COMPLETION MISSION

## ROLE AND OBJECTIVE

Act as the principal software architect, senior full-stack engineer, AI systems engineer, product designer, security reviewer, QA engineer, and release engineer responsible for bringing Momentum AI to a production-ready release candidate.

This is an existing application, not a greenfield project.

Your mission is to transform the current implementation into a reliable, beautiful, secure, marketable, multi-user AI-powered personal growth and productivity platform.

Do not merely produce a plan or mockups. Inspect the existing repository, improve the implementation, build missing realistic capabilities, test the actual application, and provide evidence of completion.

Prioritize working software over superficial complexity.

Do not claim the application is bug-free or production-ready without sufficient evidence.

## 1. REPOSITORY DISCOVERY AND PROJECT CONTEXT

Project: Momentum AI

Expected repository location on the user's Windows computer:

`C:\Users\DELL\Documents\Sam file\MomentumAI`

First inspect the actual repository and establish the current state.

Read:

- AGENTS.md and relevant agent instructions, if present.
- All relevant `.agent/*.md` planning, progress, task, architecture, and decision files.
- Backend and frontend README files.
- Existing API routes and schemas.
- Database models, migrations, RLS policies, and grants.
- Authentication implementation.
- AI provider, planning, and conversation modules.
- Existing tests, configuration, and deployment files.
- Git status and recent commits.

Treat the repository as the source of truth. The following summary is historical context, not proof of the current implementation.

Existing stack:

- React, TypeScript, Vite, Tailwind CSS v4.
- Python and FastAPI.
- Neon Auth.
- Neon PostgreSQL with row-level security.
- Restricted PostgreSQL runtime role `momentum_app`.
- Google Gemini through a replaceable provider adapter.

Previously implemented capabilities include:

- User authentication.
- Personalized onboarding.
- Goals, projects, tasks, learning, academics, and opportunities.
- Personalized dashboard.
- Gemini conversational assistant.
- Structured AI planning.
- Safe Markdown rendering.
- Persistent conversation history.
- Light and dark themes.

Database migrations 001–004 have reportedly been applied to the Neon development branch, including restricted grants. Verify their state safely; do not rerun successful migrations.

Preserve working functionality, existing user data, and architectural decisions unless a change is justified.

## 2. COMPUTER USE AND AUTONOMOUS VERIFICATION

Use available computer-use, terminal, browser, and development tools to inspect and test the real application.

When permitted:

- Open the repository in the development environment.
- Run frontend and backend development servers.
- Navigate the application in a real browser.
- Inspect browser console errors.
- Inspect Network requests and HTTP responses.
- Exercise real authentication and application workflows.
- Test responsive layouts at desktop, tablet, and mobile sizes.
- Capture screenshots and compare them against the design requirements.
- Fix reproducible problems and retest them.

Use existing authenticated development sessions only when authorized.

If a tool, desktop session, credential, or browser capability is unavailable, state the limitation and request the smallest necessary user intervention.

Do not claim to have performed computer testing unless it actually happened.

Do not access unrelated personal files or accounts.

Never disclose, print, or commit credentials, API keys, session cookies, bearer tokens, or private user records.

## 3. PRODUCT VISION

Momentum AI is a personalized AI assistant that helps people:

1. Set meaningful goals.
2. Plan and execute projects.
3. Manage tasks and deadlines.
4. Learn new skills.
5. Prepare for interviews and assessments.
6. Discover real-world opportunities.
7. Monitor academic and professional progress.
8. Receive timely reminders and accountability.
9. Reflect on progress and adjust plans.
10. Build consistent habits toward long-term ambitions.

The platform must serve different user types, not just software developers.

Personalize the experience based on each user's onboarding preferences, saved workspace records, approved memories, and explicit requests.

Never assume all users share the developer's career goals.

The core product promise is:

"Turn your goals into progress, with an AI assistant that helps you plan, learn, discover, and follow through."

## 4. PRODUCT DESIGN AND USER EXPERIENCE

Redesign and refine the entire application into a cohesive premium SaaS experience.

Design references:

- https://linear.app
- https://www.raycast.com
- https://www.pinterest.com/search/pins/?q=premium%20productivity%20dashboard%20ui
- https://www.pinterest.com/search/pins/?q=modern%20light%20dashboard%20ui
- https://www.pinterest.com/search/pins/?q=ai%20dashboard%20ui%20design

Use these as inspiration, not templates to copy.

Establish a consistent visual system:

- Refined typography and spacing.
- Consistent navigation and iconography.
- Elegant cards, forms, dialogs, tables, and empty states.
- Sophisticated light and dark themes.
- Tasteful violet/indigo brand accents.
- Subtle gradients where appropriate.
- Smooth, purposeful animations.
- Accessible contrast and keyboard navigation.
- Responsive layouts.
- Reduced-motion support.
- Skeleton loading states.
- Clear validation, success, and error feedback.
- Consistent visual hierarchy.

Do not simply add gradients, shadows, or animations everywhere.

Every major screen should feel like part of the same product.

Improve:

- Landing page and first-time experience.
- Sign-in and sign-up.
- Onboarding.
- Dashboard.
- AI Assistant.
- Projects.
- Tasks.
- Goals.
- Learning.
- Academics.
- Opportunities.
- Notifications.
- Account settings.
- Mobile navigation.

Create reusable components and semantic design tokens instead of duplicating styles.

Review actual screenshots and iterate on the result.

## 5. AUTHENTICATION — CRITICAL PRIORITY

The application has experienced intermittent access-token rejection on first page load.

Users sometimes need to press Retry multiple times before Overview works.

This must be investigated before expanding the application.

Trace:

- Neon Auth session restoration.
- Access-token acquisition and refresh.
- JWT type and expiry.
- Issuer, audience, signature, and key selection.
- Frontend/backend authentication agreement.
- Concurrent protected requests.
- Differences between initial failures and successful retries.

Use actual browser Network evidence and sanitized backend logs.

Fix confirmed root causes.

Do not weaken authentication, bypass RLS, or mask failures with arbitrary delays.

Improve the user-facing authentication experience.

Requirements:

- Clean and premium authentication pages.
- Simple sign-in/sign-up.
- Prominent Google sign-in where supported and correctly configured.
- Appropriate email verification and password recovery.
- Reliable session restoration.
- Secure sign-out.
- Clear account menu.
- Protected routes.
- Friendly error handling.
- No repeated refreshes required.
- No redirect loops.

Do not implement an insecure custom authentication system when the existing provider can satisfy the requirements.

## 6. DASHBOARD AND PRODUCTIVITY

Improve the existing dashboard using real authenticated records.

Include useful views of:

- Goals.
- Active projects.
- Outstanding tasks.
- Completed work.
- Upcoming deadlines.
- Learning progress.
- Academic commitments.
- Saved opportunities.
- Today's priorities.
- Reminders and scheduled activities.
- Relevant AI recommendations.

Make quick actions functional.

Support practical workflows:

- Create and edit goals.
- Create projects and milestones.
- Create tasks and subtasks.
- Assign priorities and deadlines.
- Link tasks to projects and goals.
- Track progress and completion.
- Organize learning activities.
- Manage academic deadlines.
- Save and track opportunities.
- Search, filter, and sort records.

Inspect the existing data model before adding new tables or features.

Only implement additional complexity when it materially improves usability.

Never show fabricated metrics.

## 7. AI ASSISTANT — THE CORE EXPERIENCE

Build a polished conversational AI workspace, not a mandatory planning form.

The assistant should support natural conversations about:

- Productivity.
- Learning.
- Projects.
- Career development.
- Academics.
- Interview preparation.
- Opportunities.
- General questions.
- Planning and decision-making.

Requirements:

- Real Gemini responses.
- Replaceable AI provider architecture.
- Persistent conversation history.
- New, rename, reopen, and delete chat.
- Multi-turn context.
- Safe Markdown rendering.
- Code blocks and readable formatting.
- Clear loading and failure states.
- Cancellation and retry handling.
- Appropriate conversation titles.
- Responsive chat interface.
- Bounded context retrieval.
- No fake AI responses.

Implement reliable response streaming if the architecture supports it safely, including cancellation and partial-response handling.

Do not treat interrupted output as a completed assistant response.

Improve the assistant's conversational behavior.

It should be capable of teaching, explaining, questioning, guiding, and adapting to the user without producing unnecessarily long information dumps.

Use saved user context only when relevant.

## 8. AI TUTORING AND LEARNING

Implement a dedicated learning experience.

Capabilities should include:

- Personalized learning goals.
- Structured learning paths.
- Interactive lessons.
- Progressive explanations.
- Practical examples.
- Practice exercises.
- Quizzes.
- Answer evaluation.
- Constructive feedback.
- Difficulty adjustment.
- Progress tracking.
- Revision recommendations.

A user should be able to say:

"Teach me SQL from beginner to advanced."

Momentum AI should establish an appropriate learning path, teach incrementally, ask questions, evaluate answers, and track progress.

Do not automatically mark a skill mastered merely because a user read an explanation.

Keep learning data isolated by authenticated user.

## 9. INTERVIEW AND ASSESSMENT PREPARATION

Implement an interview preparation workspace.

Support:

- Technical interview practice.
- Behavioral interviews.
- Role-specific question generation.
- Mock interview sessions.
- Follow-up questions.
- Answer evaluation.
- Clear scoring rubrics.
- Explanations and improvement suggestions.
- Session history.
- Progress tracking.

Avoid presenting AI-generated scores as objective hiring predictions.

Allow users to choose their target role, experience level, and interview format.

## 10. REAL OPPORTUNITY DISCOVERY

Implement genuine external opportunity discovery.

Support relevant categories:

- Internships.
- Graduate programs.
- Scholarships.
- Hackathons.
- Fellowships.
- Jobs.
- Training programs.
- Competitions.

Requirements:

- Use legitimate external search APIs, feeds, or authorized sources.
- Respect source terms and rate limits.
- Do not invent opportunities.
- Display source URLs.
- Include application deadlines when verified.
- Distinguish verified facts from inferred details.
- Explain why an opportunity matches the user.
- Support location, remote, category, and eligibility filters.
- Save opportunities to the user's workspace.
- Track application status.
- Handle expired or unavailable listings.
- Deduplicate results.

Do not pretend Gemini alone provides verified live web search.

If a search provider requires an API key or paid subscription, present the options and obtain approval before introducing costs.

## 11. PERSONALIZED MEMORY

Distinguish:

A. Conversation history.
B. Workspace records.
C. Approved long-term AI memory.

Implement user-controlled long-term memory.

Requirements:

- Clear memory proposal and approval flow.
- View and correct saved memories.
- Delete memories.
- Relevant retrieval.
- User ownership and RLS.
- Avoid unnecessary sensitive data collection.
- Do not silently save every conversation as permanent memory.
- Provide controls for disabling personalization where appropriate.

AI memory must enhance the experience without overriding explicit user instructions.

## 12. REMINDERS AND NOTIFICATIONS

Build a reliable reminder and notification system.

Support:

- Task reminders.
- Project deadlines.
- Academic deadlines.
- Opportunity deadlines.
- Learning sessions.
- User-created reminders.
- Daily planning reminders.
- Optional morning and evening check-ins.
- Snooze and dismissal.
- Notification history.
- Time-zone-aware scheduling.
- Quiet hours.
- User notification preferences.

Delivery channels:

1. In-app notifications.
2. Desktop browser push notifications.
3. Mobile web push notifications where supported.
4. Optional email notifications.

Investigate a Progressive Web App implementation for supported mobile devices.

For iOS, follow the supported Home Screen web-app push notification requirements.

Use a server-side scheduler or durable background job mechanism appropriate for the deployment environment.

Do not rely on a browser tab remaining open for scheduled delivery.

Implement:

- Permission requests.
- Push subscriptions.
- Secure subscription storage.
- Subscription cleanup.
- Delivery retry policies.
- Deduplication.
- Failure monitoring.
- Idempotent scheduling.
- Cancellation and rescheduling.
- Quiet-hours enforcement.

Push notifications require user permission and compatible device/browser support.

Do not promise guaranteed delivery when a device is offline or push services are unavailable.

Provide a clear notification settings page and a test notification action.

Do not introduce paid SMS or messaging services without approval.

## 13. CONTROLLED AI ACTIONS

Develop a safe action architecture allowing Momentum AI to propose changes such as:

- Creating a task.
- Updating a deadline.
- Scheduling a study session.
- Saving an opportunity.
- Adjusting a plan.
- Creating a reminder.

Use structured tool definitions, authorization checks, and auditable execution.

Require explicit user approval before consequential changes.

Never allow the AI to bypass normal backend authorization or directly execute unrestricted SQL.

Separate recommendations from completed actions.

Provide clear confirmation and failure states.

## 14. DATA SECURITY AND BACKEND QUALITY

Review the entire FastAPI and PostgreSQL architecture.

Requirements:

- Secure authentication.
- RLS on user-owned data.
- Restricted runtime database permissions.
- Input validation.
- Safe error handling.
- Consistent API contracts.
- Rate limiting.
- Request size limits.
- AI cost and token controls.
- Timeouts.
- Appropriate idempotency.
- Database constraints and indexes.
- Transaction safety.
- Pagination.
- Structured sanitized logging.
- Observability.
- Secure environment configuration.
- Dependency security review.
- Safe CORS configuration.
- No leaked secrets.

Test that one user cannot access another user's data through direct API requests or guessed record IDs.

Do not disable security protections to make tests pass.

## 15. PERFORMANCE AND ACCESSIBILITY

Improve:

- Frontend bundle size.
- Route-level loading.
- Unnecessary rerenders.
- API request efficiency.
- Database query performance.
- Perceived loading speed.
- Keyboard navigation.
- Screen-reader compatibility.
- Color contrast.
- Mobile layouts.
- Form accessibility.
- Error recovery.

Avoid unnecessary dependencies and premature optimization.

## 16. TESTING AND QUALITY ASSURANCE

Create a comprehensive test strategy.

Include:

- Backend unit tests.
- Frontend component tests.
- API integration tests.
- Real PostgreSQL/RLS isolation tests.
- Authentication lifecycle tests.
- Conversation persistence tests.
- AI provider failure tests.
- Notification scheduling tests.
- Opportunity source validation tests.
- End-to-end browser tests.
- Responsive layout checks.
- Accessibility checks.
- Security-focused regression tests.

Use synthetic test accounts and records.

Mock AI providers in automated tests where appropriate to avoid unnecessary costs.

Perform limited real AI integration tests to confirm the provider works.

Test real user workflows, not just isolated functions.

Maintain a reproducible bug register.

For every confirmed defect:

1. Reproduce.
2. Identify the root cause.
3. Implement the smallest sound fix.
4. Add regression coverage.
5. Retest in the browser where relevant.

Do not claim zero bugs.

Report unresolved risks and coverage gaps honestly.

## 17. DEPLOYMENT AND RELEASE ENGINEERING

Prepare the application for a genuine production deployment.

Review:

- Frontend hosting.
- FastAPI hosting.
- Neon production database branch.
- Database migration strategy.
- Secure secrets management.
- Production CORS and domains.
- HTTPS.
- Background worker hosting.
- Push notification infrastructure.
- Monitoring and alerting.
- Error tracking.
- Database backups and recovery.
- Health checks.
- CI/CD.
- Deployment rollback.
- Environment separation.
- AI usage limits and cost monitoring.

Create clear deployment instructions and an operational runbook.

Do not deploy to production, purchase services, create paid resources, change DNS, or run destructive production migrations without explicit approval.

## 18. MARKET READINESS

Improve the product's commercial presentation.

Deliver:

- Clear product positioning.
- A compelling landing page.
- Useful feature explanations.
- Professional onboarding.
- Product tour or helpful first-use guidance.
- Privacy policy and terms drafts for review.
- Support/contact workflow.
- Feedback mechanism.
- Account deletion and data handling controls.
- Transparent AI and notification permissions.
- Clear limitations and service expectations.

Do not invent customer testimonials, user counts, certifications, or pricing claims.

Billing and subscriptions are optional future capabilities. Do not introduce a payment provider without approval.

## 19. IMPLEMENTATION STRATEGY

This is a comprehensive mission, but it must not become one uncontrolled rewrite.

Execute in phases:

PHASE 0 — Repository audit, product architecture, bug register, and release plan.

PHASE 1 — Fix authentication, Gemini reliability, conversation persistence, and critical security defects.

PHASE 2 — Premium design system, authentication UX, responsive dashboard, and consistent application UI.

PHASE 3 — Complete and polish core productivity workflows.

PHASE 4 — Conversational AI, planning, personalization, and safe memory.

PHASE 5 — Interactive tutoring and interview preparation.

PHASE 6 — Real opportunity discovery.

PHASE 7 — Reminders, notifications, mobile PWA, and proactive check-ins.

PHASE 8 — Controlled AI actions and approval workflows.

PHASE 9 — Production hardening, full browser testing, performance, accessibility, documentation, and release preparation.

The sequence may be adjusted based on verified dependencies and risks.

For each phase:

- Define acceptance criteria.
- Implement the scoped work.
- Run relevant tests.
- Inspect real browser behavior.
- Fix regressions.
- Update tracking documentation.
- Record remaining risks.
- Proceed only when the milestone is sufficiently verified.

Avoid repeatedly asking the user to perform routine tests that the available tools can execute.

Use the user's intervention only for authentication, external credentials, service approvals, or inaccessible environments.

## 20. GIT AND DELIVERY RULES

Inspect Git status before modifying files.

Preserve existing user changes.

Use meaningful, small commits at verified milestones when authorized.

Do not force-push, rewrite history, or discard uncommitted work.

Do not push to GitHub without explicit authorization.

Before requesting push approval:

- Run automated checks.
- Review changes for secrets.
- Confirm .env files are ignored.
- Confirm the production build succeeds.
- Confirm required migrations are documented.
- Update README and setup instructions.

## 21. FINAL DELIVERABLES

Produce:

1. A working, polished Momentum AI application.
2. A documented architecture.
3. A complete feature inventory.
4. A verified bug-fix report.
5. A database migration and permissions record.
6. Automated test results.
7. Browser test evidence.
8. A security review summary.
9. A deployment guide.
10. A GitHub-ready repository.
11. A release checklist.
12. A concise list of remaining limitations and operational costs.

Classify features as:

- Implemented and verified.
- Implemented but not fully verified.
- Blocked by external dependencies.
- Deferred to a later release.

Never claim features are complete simply because code exists.

## 22. START NOW

Begin by reading the repository and all relevant Markdown project documentation.

Perform the audit, establish the actual state, and create an evidence-based execution plan.

Then begin Phase 1 reliability fixes and proceed autonomously through subsequent phases as the available tools, permissions, and verified checkpoints allow.

Keep progress updates concise and meaningful.

Ask for approval only when a decision involves cost, credentials, destructive operations, production changes, or other consequential external actions.

The goal is not a flashy prototype.

The goal is a dependable, polished, useful, secure, and commercially credible Momentum AI release candidate.