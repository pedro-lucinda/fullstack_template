"""Business logic for the todos module, kept separate from the HTTP layer
(`router.py`) so it stays framework-agnostic — e.g. reusable from a worker,
a CLI, or (if this module is ever split out) a standalone microservice's own
transport layer, without dragging FastAPI request/response concerns along.
"""

import json
import uuid

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.todos.models import Todo
from app.modules.todos.schemas import TodoRead

# Cache-aside example: list_todos is read far more often than todos are
# written, so its result is cached per-user for a short TTL and explicitly
# invalidated on every write (create/toggle/delete) below. The short TTL is a
# safety net in case an invalidation is ever missed; it isn't load-bearing.
TODOS_CACHE_TTL_SECONDS = 30


def _cache_key(owner_id: str) -> str:
    return f"todos:{owner_id}"


async def create_todo(db: AsyncSession, redis: Redis, owner_id: str, title: str) -> Todo:
    """Create a new todo owned by `owner_id` and invalidate its list cache."""
    todo = Todo(owner_id=owner_id, title=title)
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    await redis.delete(_cache_key(owner_id))
    return todo


async def list_todos(db: AsyncSession, redis: Redis, owner_id: str) -> list[Todo] | list[dict]:
    """List `owner_id`'s todos, newest first.

    Cached per-user in Redis for `TODOS_CACHE_TTL_SECONDS`; see the cache-aside
    note above the module-level constant. Returns plain dicts on a cache hit
    (already-serialized `TodoRead` shape) or ORM instances on a miss — FastAPI's
    `response_model` handles both.
    """
    cache_key = _cache_key(owner_id)
    cached = await redis.get(cache_key)
    if cached is not None:
        return json.loads(cached)

    result = await db.execute(
        select(Todo).where(Todo.owner_id == owner_id).order_by(Todo.created_at.desc())
    )
    todos = list(result.scalars().all())

    serialized = [TodoRead.model_validate(todo).model_dump(mode="json") for todo in todos]
    await redis.set(cache_key, json.dumps(serialized), ex=TODOS_CACHE_TTL_SECONDS)

    return todos


async def get_owned_todo(db: AsyncSession, todo_id: uuid.UUID, owner_id: str) -> Todo | None:
    """Fetch a todo by id, scoped to its owner. `None` if missing or not owned.

    Callers (the router) turn a `None` into a 404 rather than a 403, so we
    don't leak whether a todo owned by someone else exists at all.
    """
    result = await db.execute(select(Todo).where(Todo.id == todo_id, Todo.owner_id == owner_id))
    return result.scalar_one_or_none()


async def toggle_todo(db: AsyncSession, redis: Redis, todo: Todo) -> Todo:
    """Flip a todo's `completed` flag and invalidate its owner's list cache."""
    todo.completed = not todo.completed
    await db.commit()
    await db.refresh(todo)
    await redis.delete(_cache_key(todo.owner_id))
    return todo


async def delete_todo(db: AsyncSession, redis: Redis, todo: Todo) -> None:
    """Delete a todo and invalidate its owner's list cache."""
    await db.delete(todo)
    await db.commit()
    await redis.delete(_cache_key(todo.owner_id))
