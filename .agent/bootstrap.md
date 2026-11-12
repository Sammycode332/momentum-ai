# Local Bootstrap Procedure

This procedure records the FND-01 implementation and verification workflow approved in ADR-010. It is a local development baseline only; it does not select deployment, environment/configuration conventions, test tooling, API versioning, or an API error format.

## Frontend (`frontend/`)

The frontend will use the standard React + TypeScript + Vite scaffold, Tailwind CSS v4 through its Vite integration, npm, and a frontend-local `package-lock.json`.

From `frontend/`:

```powershell
npm install
npm run dev
npm run build
npm run lint
```

`npm run dev` is a long-running development command. Verify that it starts successfully, then stop it with `Ctrl+C` before running subsequent checks in the same terminal. `npm run build` verifies the production build, and `npm run lint` verifies the scaffold's configured linting.

## Backend (`backend/`)

The backend will use FastAPI, a standard `pyproject.toml`, a Python virtual environment with pip, Uvicorn, and a minimal `app/main.py` application module. The `pyproject.toml` must provide valid installable project metadata and declare the minimal FastAPI and Uvicorn dependencies so `python -m pip install -e .` works. The commands below use PowerShell.

From `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m uvicorn app.main:app --reload
```

For a basic import verification after installation, run:

```powershell
python -c "from app.main import app; assert app is not None"
```

`python -m uvicorn app.main:app --reload` is a long-running development command. For startup verification, run it and confirm that it reports successful application startup, then stop it with `Ctrl+C` before running subsequent checks in the same terminal. No custom application HTTP endpoints, including `/health`, are created during FND-01. FastAPI's framework-generated documentation and OpenAPI routes may remain enabled.

## Deferred choices

FND-01 does not introduce pnpm workspaces, Turborepo, Nx, Docker, Poetry, uv, a root task runner, a UI component library, a backend test framework, Supabase configuration, secrets, database migrations, authentication, CORS configuration, or frontend-to-backend API communication. These need their own approved tasks and decisions.
