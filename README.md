# Fullstack Template

A batteries-included fullstack template with a typed contract between frontend
and backend, an authenticated auth flow via Auth0, and a spec-driven development
workflow inspired by AWS's agentic SDLC.

## Stack

**Frontend** (`apps/frontend`)
- Vite + React + TypeScript
- Tailwind CSS + shadcn/ui-style components (`src/components/ui`)
- Zustand for state management (no React Context)
- Auth0 React SDK for authentication
- [Kubb](https://kubb.dev) generates a fully-typed API client from the backend's OpenAPI spec
- Jest + Testing Library for unit tests
- Playwright for end-to-end tests

**Backend** (`apps/backend`)
- FastAPI + SQLAlchemy (async) + Alembic migrations
- PostgreSQL
- Redis — caches the Auth0 JWKS lookup and the todos list endpoint (cache-aside,
  invalidated on writes); see `app/core/redis.py`
- Auth0 JWT verification (JWKS-based)
- LangChain example agent (`app/modules/agent/`) — a tool-calling agent exposed at
  `POST /api/v1/agent/chat`, see `specs/agent-chat/`
- uv for dependency/environment management
- pytest for tests

**Shared**
- `packages/api-spec` — the OpenAPI spec exported from FastAPI; single source of
  truth for the HTTP contract, consumed by Kubb.
- `specs/` — spec-driven development docs (requirements → design → tasks) per
  feature. See `specs/README.md`.
- Turborepo + pnpm workspaces to orchestrate `dev`/`build`/`test`/`lint` across
  both apps from the repo root.

## Getting Started

### Option A: Docker Compose (recommended, dev only)

```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env
# fill in your Auth0 tenant details in both .env files
# optionally set OPENAI_API_KEY in apps/backend/.env to use the example agent
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (docs at /docs)
- Postgres: localhost:5432
- Redis: localhost:6379

The backend container runs Alembic migrations automatically on startup.

### Option B: Run locally

**Backend:**
```bash
cd apps/backend
uv sync
cp .env.example .env   # point POSTGRES_*/REDIS_* vars at your local Postgres/Redis, add Auth0 config
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Redis is required — the app fails at request time (not at startup) if it can't
reach it, since the client connects lazily. Run one locally with e.g.
`docker run --rm -p 6379:6379 redis:7-alpine`.

**Frontend:**
```bash
pnpm install            # from repo root
cd apps/frontend
cp .env.example .env    # add your Auth0 SPA app config
pnpm dev
```

## Regenerating the API client

Whenever you change a FastAPI route/schema:

```bash
cd apps/backend && uv run python -m app.scripts.export_openapi
cd ../frontend && pnpm generate:api
```

(Or `pnpm generate:api` from the repo root once both are set up — see `turbo.json`.)
Never hand-edit files in `apps/frontend/src/api/generated`.

## Testing

```bash
pnpm test        # Jest (frontend) + pytest (backend), via turbo
pnpm test:e2e    # Playwright (requires an Auth0 test user, see apps/frontend/e2e)
pnpm lint        # ruff (backend) + eslint (frontend)
pnpm typecheck   # tsc
```

## Spec-Driven Development

New features start as a spec in `specs/<feature-name>/` (requirements → design →
tasks) before any code is written. See `specs/README.md` for the full workflow
and `specs/todos/` for a worked example matching the included sample Todos
feature.

## Repository Layout

```
apps/
  frontend/         Vite + React + TS app
  backend/          FastAPI app, organized as a modular monolith:
                       app/modules/<name>/  One package per business domain
                                            (router.py, service.py, models.py,
                                            schemas.py) — see `todos/`, `agent/`.
                       app/core/            Shared platform code only (config,
                                            db, redis, auth) — no business logic.
packages/
  api-spec/         Generated OpenAPI spec (source of truth for the API contract)
specs/
  _template/        Copy this to start a new feature spec
  todos/            Worked example spec for the included sample feature
docker-compose.yml  Dev-only orchestration (Postgres + Redis + backend + frontend)
```

The backend's module boundaries are intentionally microservice-shaped: each
`app/modules/<name>/` package only depends on `app/core/` and itself, never on
another module's internals. Splitting one out later means copying its folder
(plus whatever `app/core/` pieces it needs) into a new service — no
disentangling required.
