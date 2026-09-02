# fullstack_template — Agent Instructions

Monorepo: FastAPI/Postgres/Auth0 backend + LangChain example agent, Vite/React/TS/Tailwind
backend/frontend, spec-driven development. Read this whole file before making changes; the
GitNexus section below (auto-maintained, do not hand-edit between the markers) gives structural
code-intelligence tools — use it instead of blind grepping when exploring or assessing impact.

## Layout

- `apps/backend` — FastAPI + SQLAlchemy (async) + Alembic + Postgres + Auth0 JWT auth, managed
  with `uv`. LangChain example agent under `app/agents/`.
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

- All I/O in request paths must be async — no blocking `httpx.get`/`requests.get` calls inside
  `async def`. Use `httpx.AsyncClient` (see `app/core/auth.py` for the JWKS-fetch pattern).
- Route prefixes use the `API_V1_PREFIX` constant from `app/core/constants.py`, not a literal
  `"/api/v1"` string.
- Ownership checks return **404, not 403**, when a resource exists but belongs to another user
  (avoids leaking existence — see `_get_owned_todo` in `app/api/routes/todos.py`).
- `ruff` config (`apps/backend/pyproject.toml`) ignores `B008` (FastAPI's idiomatic
  `Depends()` default triggers a bugbear false positive) and excludes `alembic/versions`/
  `alembic/env.py` from linting.
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