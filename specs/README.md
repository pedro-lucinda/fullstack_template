# Spec-Driven Development (SDLC)

This repository follows a **spec-driven development workflow**, modeled after AWS's
agentic SDLC approach (as used by tools like Kiro / AWS's spec-driven agents). Every
non-trivial feature is designed *before* it is coded, using three documents that live
in `specs/<feature-name>/`:

1. **`requirements.md`** — What we're building and why.
   - Written as user stories with acceptance criteria in **EARS** notation
     ("Easy Approach to Requirements Syntax"): `WHEN <trigger> THE SYSTEM SHALL <response>`.
   - No implementation details. Focused on observable behavior.

2. **`design.md`** — How we're building it.
   - Architecture/data-flow, data model changes, API contract (request/response
     shapes, status codes, error cases), state management shape, and edge cases.
   - The API contract described here becomes the FastAPI route + Pydantic schemas,
     which in turn generate the `openapi.json` used by Kubb for the frontend client.

3. **`tasks.md`** — The ordered, checkable implementation plan.
   - Discrete, verifiable steps (backend model → migration → route → tests →
     regenerate client → frontend store/hook → UI → tests).
   - Each task references the requirement(s) it satisfies.

## Workflow

```
specs/<feature>/requirements.md   (agree on WHAT)
        ↓
specs/<feature>/design.md         (agree on HOW, incl. API contract)
        ↓
specs/<feature>/tasks.md          (break down the work)
        ↓
Implement backend → export OpenAPI spec → generate frontend client (Kubb) → implement UI
        ↓
Tests (pytest, Jest, Playwright) prove the acceptance criteria from requirements.md
```

## Rules

- The **OpenAPI spec is the single source of truth** for the HTTP contract between
  frontend and backend. It is generated from the FastAPI app (`pnpm --filter backend
  export:openapi` or `uv run python -m app.scripts.export_openapi`) into
  `packages/api-spec/openapi.json`, and Kubb reads from that file to generate the
  typed frontend client (`pnpm --filter frontend generate:api`). Never hand-edit
  generated client code in `apps/frontend/src/api/generated`.
- Do not start writing code for a new feature until `requirements.md` and
  `design.md` exist and are internally consistent.
- Keep `tasks.md` up to date — check items off as they land, and add new tasks if
  scope changes instead of silently deviating from the design.
- Use `specs/_template/` as the starting point for a new feature spec:
  `cp -r specs/_template specs/<feature-name>`.

See `specs/todos/` for a worked example (the sample Todos feature included in this
template).
