# Environment, Configuration, and Secrets Conventions

This document establishes the FND-02 configuration boundary. It does not select a hosting provider, secret manager, Supabase integration, AI provider, or runtime configuration library.

## Repository convention

Real environment files are ignored throughout the repository: `.env` and `.env.*`. Placeholder-only templates named `.env.example` or `.env.*.example` may be committed. Templates must contain no real credentials, project URLs, tokens, or environment-specific values.

Do not place secrets in source files, documentation examples, build artifacts, prompts, logs, error messages, or committed environment files. If a secret is accidentally committed, treat it as exposed: revoke or rotate it through the owning service and remove it through the approved incident/repository procedure.

## Environment use

### Local development

Developers may supply configuration through ignored environment files or process environment variables. The frontend's Vite tooling can load its supported `.env` files. The current FastAPI scaffold has no `.env` loader; backend settings must be injected into the process until a later, explicitly approved configuration implementation is added.

### Staging and production

The eventual hosting environment injects runtime configuration and secrets. They are configured separately for each environment and are never copied into the repository. This convention deliberately does not select a host, deployment platform, secret manager, or environment naming scheme beyond local, staging, and production.

## Public browser configuration

In Vite, variables with the `VITE_` prefix are available to browser code through `import.meta.env`. Treat every `VITE_*` value as public: it can be present in the compiled client bundle and visible to users. Use this prefix only for non-sensitive client configuration, such as a future public API base URL.

Never use `VITE_*` for credentials, private tokens, Supabase `service_role` credentials, AI API keys, database credentials, signing secrets, or other privileged material. Frontend visibility, route guards, and a publishable identifier are not authorization controls.

If Supabase is later integrated, a project URL and publishable/anon key may be public client configuration only after the associated browser access is protected and verified with RLS and server-side authorization where applicable. The Supabase `service_role` credential remains backend-only and must not enter browser code, a `VITE_*` variable, or a frontend environment file.

## Backend-only configuration

Privileged Supabase credentials, AI-provider API keys, database credentials, signing secrets, and server-only service endpoints are backend runtime configuration. Backend code must read only the configuration it needs, validate required values when that code is implemented, and avoid returning or logging values.

Choosing a backend settings library, dotenv loader, secret manager, provider SDK, exact variable names, or deployment integration is deferred until a feature needs it. Any later choice must preserve this public/private boundary and be recorded through the project decision process.

## Verification

When this convention changes, use `git check-ignore -v --no-index` to inspect the effective ignore rule for real environment paths and template exceptions. Confirm templates are trackable with `git ls-files --others --exclude-standard`. Inspect tracked filenames and the diff for accidental credential-bearing files or values, and run `git diff --check`.
