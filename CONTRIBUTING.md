# Contributing

## Workflow: Spec-Driven Development

This repo uses a spec-driven workflow for any non-trivial feature. Before writing
code:

1. Copy the template: `cp -r specs/_template specs/<feature-name>`
2. Fill in `requirements.md` (user stories + EARS acceptance criteria)
3. Fill in `design.md` (architecture, data model, **API contract**, frontend state,
   edge cases, test plan)
4. Fill in `tasks.md` (ordered, checkable implementation steps)

Only start implementing once requirements and design are settled. See
`specs/README.md` for the full rationale and `specs/todos/` for a worked example.

## Implementation order for a typical feature

1. Backend: SQLAlchemy model → Alembic migration → Pydantic schemas → route(s)
2. Backend: pytest coverage (happy paths, ownership/auth edge cases, validation)
3. Export the OpenAPI spec: `cd apps/backend && uv run python -m app.scripts.export_openapi`
4. Frontend: regenerate the typed client: `cd apps/frontend && pnpm generate:api`
5. Frontend: Zustand store wiring the generated client functions
6. Frontend: UI components consuming the store
7. Frontend: Jest tests for the store, Playwright test for the user flow
8. Update `specs/<feature>/tasks.md` (check items off) and `design.md` if the
   implementation diverged from the plan

## Conventions

- **Never hand-edit** `apps/frontend/src/api/generated/**` — it's regenerated
  from `packages/api-spec/openapi.json`. If it's wrong, fix the FastAPI route/
  schema and regenerate.
- Frontend state lives in Zustand stores (`src/store/*.ts`), not React Context.
- All authenticated backend routes depend on `get_current_user`
  (`app/core/auth.py`), which validates the Auth0 JWT via JWKS.
- Keep `packages/api-spec/openapi.json` committed and up to date — it's the
  reviewable diff of your API contract changes.

## Before opening a PR

```bash
pnpm lint
pnpm typecheck
pnpm test
```
