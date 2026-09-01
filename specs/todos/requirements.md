# Requirements: Todos

## Overview
A minimal Todos feature demonstrating the full stack: authenticated users can create,
list, complete, and delete their own todo items.

## User Stories

### US-1: Create a todo
As an authenticated user, I want to create a todo item with a title, so that I can
track something I need to do.

**Acceptance Criteria (EARS format):**
- WHEN an authenticated user submits a title of 1-200 characters THE SYSTEM SHALL
  create a todo owned by that user and return it with a generated id, `completed:
  false`, and a `created_at` timestamp.
- IF the title is empty or missing THEN THE SYSTEM SHALL reject the request with a
  `422` validation error.
- IF the request has no valid Auth0 bearer token THEN THE SYSTEM SHALL reject the
  request with a `401` error.

### US-2: List my todos
As an authenticated user, I want to see only my own todos, so that my list stays
private.

**Acceptance Criteria (EARS format):**
- WHEN an authenticated user requests their todo list THE SYSTEM SHALL return only
  todos owned by that user, ordered by `created_at` descending.

### US-3: Toggle completion
As an authenticated user, I want to mark a todo complete/incomplete, so that I can
track progress.

**Acceptance Criteria (EARS format):**
- WHEN an authenticated user toggles a todo they own THE SYSTEM SHALL flip its
  `completed` value and persist it.
- IF the todo does not belong to the requesting user THEN THE SYSTEM SHALL respond
  with a `404` (not `403`, to avoid leaking existence of other users' todos).

### US-4: Delete a todo
As an authenticated user, I want to delete a todo I own, so that I can remove
items I no longer need.

**Acceptance Criteria (EARS format):**
- WHEN an authenticated user deletes a todo they own THE SYSTEM SHALL remove it and
  return `204`.
- IF the todo does not belong to the requesting user THEN THE SYSTEM SHALL respond
  with a `404`.

## Out of Scope
- Sharing todos between users
- Due dates, priorities, tags

## Open Questions
- None
