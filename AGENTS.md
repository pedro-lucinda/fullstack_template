# fullstack_template — Agent Instructions

Monorepo: FastAPI/Postgres/Auth0 backend + LangChain example agent, Vite/React/TS/Tailwind
backend/frontend, spec-driven development. Read this whole file before making changes; the
GitNexus section below (auto-maintained, do not hand-edit between the markers) gives structural
code-intelligence tools — use it instead of blind grepping when exploring or assessing impact.

## Layout

- `apps/backend` — FastAPI + SQLAlchemy (async) + Alembic + Postgres + Redis + Auth0 JWT auth,
  managed with `uv`. Organized as a **modular monolith** (see below) so a module can be split
  out into its own microservice later with minimal rework.
- `apps/frontend` — Vite + React + TypeScript + Tailwind + shadcn-style components (hand-built
  under `src/components/ui/`) + Zustand (state only — **no React Context** for app state) +
  Auth0 React SDK, managed with `pnpm`.
- `packages/api-spec` — the shared `openapi.json`, exported from the live FastAPI app. Treat it
  as generated output, not hand-authored.
- `specs/<feature>/` — spec-driven workflow docs (`requirements.md` → `design.md` → `tasks.md`,
  AWS-SDLC/Kiro style). See `specs/README.md`. Add a new spec folder for any non-trivial feature
  before writing code.
- Root `pnpm` + `turbo` orchestrates `dev`/`build`/`lint`/`test`/`typecheck`/`generate:api`
  across both apps (see root `package.json`, `turbo.json`).

## Do not hand-edit — generated or noisy

- `apps/frontend/src/api/generated/**` — Kubb-generated API client, regenerated from
  `packages/api-spec/openapi.json` via `pnpm generate:api`. Editing a route/schema on the
  backend without regenerating this (and the spec) is the most common way to introduce drift.
- `packages/api-spec/openapi.json` — exported via
  `cd apps/backend && uv run python -m app.scripts.export_openapi`. Re-run after any route or
  Pydantic schema change, then regenerate the Kubb client.
- `apps/backend/alembic/versions/**` — Alembic auto-generated migrations.
- `pnpm-lock.yaml`, `.turbo/**`, `dist/**`, `build/**`, `apps/frontend/.kubb/**` — build/tooling
  artifacts.

## Backend conventions

- **Modular-monolith layout**: each business domain lives under `app/modules/<name>/` as a
  self-contained package — `router.py` (FastAPI routes, HTTP concerns only), `service.py`
  (business logic, framework-agnostic), `models.py` (SQLAlchemy ORM), `schemas.py` (Pydantic
  request/response models). See `app/modules/todos/` and `app/modules/agent/`. `app/core/` holds
  only cross-cutting platform concerns shared by every module (`config.py`, `db.py`, `redis.py`,
  `auth.py`, `constants.py`).
  - **New features**: add a new `app/modules/<name>/` package rather than growing an existing
    one or adding top-level `app/api|models|schemas` folders — that layered-by-technical-concern
    structure was intentionally replaced by layering-by-domain.
  - **Rule of thumb for microservice extraction**: a module should only import from `app.core`
    and its own package, never reach into another module's `models`/`service` internals — treat
    cross-module calls the same way you'd treat a call to another service (i.e. avoid them, or
    go through a public interface). This is what keeps `app/modules/<name>/` copy-pasteable into
    a standalone service later (bringing along whichever bits of `app/core` it needs).
- All I/O in request paths must be async — no blocking `httpx.get`/`requests.get` calls inside
  `async def`. Use `httpx.AsyncClient` (see `app/core/auth.py` for the JWKS-fetch pattern).
- Route prefixes use the `API_V1_PREFIX` constant from `app/core/constants.py`, not a literal
  `"/api/v1"` string.
- Ownership checks return **404, not 403**, when a resource exists but belongs to another user
  (avoids leaking existence — see `_get_owned_todo_or_404` in `app/modules/todos/router.py`).
- `ruff` config (`apps/backend/pyproject.toml`) ignores `B008` (FastAPI's idiomatic
  `Depends()` default triggers a bugbear false positive) and excludes `alembic/versions`/
  `alembic/env.py` from linting.
- Redis (`app/core/redis.py`, `get_redis`) is used for the Auth0 JWKS cache (`app/core/auth.py`)
  and as a cache-aside example on `GET /api/v1/todos` (invalidated on every write in
  `app/modules/todos/service.py`). Tests override `get_redis` with `fakeredis` — see
  `tests/conftest.py` — so they never need a live Redis instance.
- **Observability**: `app/core/logging.py` configures `structlog` (JSON in prod via
  `LOG_FORMAT=json`, human-readable console in dev); `app/core/middleware.py` binds a
  per-request `request_id` (from/echoed as the `X-Request-ID` header) into structlog's
  contextvars and logs one access-log line per request. `GET /health/live` is a static
  liveness probe; `GET /health/ready` (via `Depends(get_db)`/`Depends(get_redis)`, so tests can
  override it the normal way) actually pings Postgres and Redis and returns `503` if either is
  down. OpenTelemetry tracing (`app/core/telemetry.py`) and Sentry (`app/core/sentry.py`) are
  both opt-in no-ops unless `OTEL_ENABLED=true` / `SENTRY_DSN` is set — safe to import in tests
  without any collector/DSN configured.
- Verified commands: `cd apps/backend && uv run ruff check . && uv run pytest`.

## Frontend conventions

- State management is **Zustand only** — do not introduce React Context for app state.
- All backend calls go through the Kubb-generated client (`src/api/generated/clients/*`) via
  the custom fetch wrapper in `src/api/client.ts` (attaches the Auth0 access token). Never call
  `fetch`/`axios` directly from components or stores.
- `import.meta.env` access is isolated in `src/lib/env.ts` (mapped to a Jest mock via
  `moduleNameMapper` in `jest.config.cjs`) — add new env vars there, not inline.
- Verified commands: `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` (from repo root or
  `apps/frontend`).

## Quality gates

- Git hooks (see `lefthook.yml` if present) and CI (`.github/workflows/ci.yml`) run ruff/eslint/
  tsc/pytest plus ast-grep rules and OpenAPI/Kubb drift checks — see those files for the
  authoritative, up-to-date list rather than duplicating it here.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **fullstack_template** (406 symbols, 487 relationships, 3 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/fullstack_template/context` | Codebase overview, check index freshness |
| `gitnexus://repo/fullstack_template/clusters` | All functional areas |
| `gitnexus://repo/fullstack_template/processes` | All execution flows |
| `gitnexus://repo/fullstack_template/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->