# Design: Todos

## Architecture Overview
Standard flow: React page → Zustand `useTodoStore` → Kubb-generated typed client
(`apps/frontend/src/api/generated`) → FastAPI route (`/api/v1/todos`) → SQLAlchemy
model → Postgres. All routes require a valid Auth0-issued JWT, validated via a
FastAPI dependency (`get_current_user`) that verifies the token signature against
Auth0's JWKS endpoint and extracts the `sub` claim as the user id.

## Data Model
Table `todos` (`apps/backend/app/modules/todos/models.py`):
- `id: UUID` (PK, server-generated)
- `owner_id: str` (Auth0 `sub` claim, indexed)
- `title: str` (max 200)
- `completed: bool` (default `false`)
- `created_at: datetime` (server default `now()`)

Migration: `apps/backend/alembic/versions/<rev>_create_todos_table.py`.

## API Contract

### `POST /api/v1/todos`
- **Auth:** required
- **Request body:**
  ```json
  { "title": "Buy milk" }
  ```
- **Success response (`201`):**
  ```json
  { "id": "uuid", "title": "Buy milk", "completed": false, "created_at": "2024-01-01T00:00:00Z" }
  ```
- **Error responses:** `422` invalid body, `401` missing/invalid token

### `GET /api/v1/todos`
- **Auth:** required
- **Success response (`200`):** array of todo objects (see above), owned by caller only.

### `PATCH /api/v1/todos/{id}/toggle`
- **Auth:** required
- **Success response (`200`):** the updated todo object.
- **Error responses:** `404` if not found / not owned by caller, `401`.

### `DELETE /api/v1/todos/{id}`
- **Auth:** required
- **Success response:** `204` empty body.
- **Error responses:** `404` if not found / not owned by caller, `401`.

## Frontend State
`apps/frontend/src/store/todoStore.ts` — Zustand store holding `todos: Todo[]`,
`isLoading`, `error`, and actions `fetchTodos`, `addTodo`, `toggleTodo`,
`removeTodo` that call the Kubb-generated hooks/functions and update local state
optimistically on success.

## Edge Cases & Error Handling
- Empty title → client-side disables submit button; server still validates (422).
- Toggling/deleting another user's todo → `404`, surfaced as a toast in the UI.
- Network/API failure → store sets `error` and UI shows an inline retry affordance.

## Test Plan
- **Backend (pytest):** create/list/toggle/delete happy paths; ownership isolation
  (user A cannot see/modify user B's todos); validation error on empty title.
- **Frontend unit (Jest):** `todoStore` actions update state correctly given mocked
  API responses (success and error cases).
- **E2E (Playwright):** logged-in user creates a todo, sees it in the list, toggles
  it complete, then deletes it.
