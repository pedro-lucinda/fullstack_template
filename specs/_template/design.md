# Design: <Feature Name>

## Architecture Overview
<How this fits into the existing backend/frontend architecture. Diagram optional.>

## Data Model
<New/changed database tables, columns, relationships. Reference the SQLAlchemy model
and Alembic migration that will implement this.>

## API Contract
> This section is the source of truth for the OpenAPI spec. Keep it in sync with the
> actual FastAPI route + Pydantic schemas once implemented.

### `<METHOD> /api/v1/<resource>`
- **Auth:** required / public (Auth0 JWT bearer token)
- **Request body / params:**
  ```json
  {}
  ```
- **Success response (`<status code>`):**
  ```json
  {}
  ```
- **Error responses:**
  - `<status code>` — <condition>

## Frontend State
<Which Zustand store owns this data, shape of the store, which generated Kubb
hooks/functions are consumed.>

## Edge Cases & Error Handling
- <Edge case> → <expected handling>

## Test Plan
- **Backend (pytest):** <what is covered>
- **Frontend unit (Jest):** <what is covered>
- **E2E (Playwright):** <user flow covered>
