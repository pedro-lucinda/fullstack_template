import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.constants import API_V1_PREFIX
from app.core.db import get_db
from app.core.redis import get_redis
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoRead

router = APIRouter(prefix=f"{API_V1_PREFIX}/todos", tags=["todos"])

# Cache-aside example: list_todos is read far more often than todos are
# written, so its result is cached per-user for a short TTL and explicitly
# invalidated on every write (create/toggle/delete) below. The short TTL is a
# safety net in case an invalidation is ever missed; it isn't load-bearing.
TODOS_CACHE_TTL_SECONDS = 30


def _todos_cache_key(owner_id: str) -> str:
    return f"todos:{owner_id}"


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
async def create_todo(
    payload: TodoCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> Todo:
    """Create a new todo owned by the authenticated user."""
    todo = Todo(owner_id=user.sub, title=payload.title)
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    await redis.delete(_todos_cache_key(user.sub))
    return todo


@router.get("", response_model=list[TodoRead])
async def list_todos(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> list[Todo] | list[dict]:
    """List the authenticated user's todos, newest first.

    Cached per-user in Redis for `TODOS_CACHE_TTL_SECONDS`; see the cache-aside
    note above the module-level constant.
    """
    cache_key = _todos_cache_key(user.sub)
    cached = await redis.get(cache_key)
    if cached is not None:
        return json.loads(cached)

    result = await db.execute(
        select(Todo).where(Todo.owner_id == user.sub).order_by(Todo.created_at.desc())
    )
    todos = list(result.scalars().all())

    serialized = [TodoRead.model_validate(todo).model_dump(mode="json") for todo in todos]
    await redis.set(cache_key, json.dumps(serialized), ex=TODOS_CACHE_TTL_SECONDS)

    return todos


async def _get_owned_todo(db: AsyncSession, todo_id: uuid.UUID, owner_id: str) -> Todo:
    """Fetch a todo by id, scoped to its owner.

    Raises a `404` (rather than `403`) when the todo doesn't exist or belongs
    to a different user, so we don't leak whether it exists at all.
    """
    result = await db.execute(select(Todo).where(Todo.id == todo_id, Todo.owner_id == owner_id))
    todo = result.scalar_one_or_none()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@router.patch("/{todo_id}/toggle", response_model=TodoRead)
async def toggle_todo(
    todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> Todo:
    """Flip a todo's `completed` flag. 404s if not owned by the caller."""
    todo = await _get_owned_todo(db, todo_id, user.sub)
    todo.completed = not todo.completed
    await db.commit()
    await db.refresh(todo)
    await redis.delete(_todos_cache_key(user.sub))
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> None:
    """Delete a todo. 404s if not owned by the caller."""
    todo = await _get_owned_todo(db, todo_id, user.sub)
    await db.delete(todo)
    await db.commit()
    await redis.delete(_todos_cache_key(user.sub))
