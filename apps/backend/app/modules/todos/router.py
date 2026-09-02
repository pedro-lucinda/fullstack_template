import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.constants import API_V1_PREFIX
from app.core.db import get_db
from app.core.redis import get_redis
from app.modules.todos import service
from app.modules.todos.models import Todo
from app.modules.todos.schemas import TodoCreate, TodoPage, TodoRead

router = APIRouter(prefix=f"{API_V1_PREFIX}/todos", tags=["todos"])


async def _get_owned_todo_or_404(db: AsyncSession, todo_id: uuid.UUID, owner_id: str) -> Todo:
    todo = await service.get_owned_todo(db, todo_id, owner_id)
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
async def create_todo(
    payload: TodoCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> Todo:
    """Create a new todo owned by the authenticated user."""
    return await service.create_todo(db, redis, user.sub, payload.title)


@router.get("", response_model=TodoPage)
async def list_todos(
    limit: int = Query(service.DEFAULT_LIMIT, ge=1, le=service.MAX_LIMIT),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> TodoPage:
    """List the authenticated user's todos, newest first, paginated."""
    return await service.list_todos(db, redis, user.sub, limit, offset)


@router.patch("/{todo_id}/toggle", response_model=TodoRead)
async def toggle_todo(
    todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> Todo:
    """Flip a todo's `completed` flag. 404s if not owned by the caller."""
    todo = await _get_owned_todo_or_404(db, todo_id, user.sub)
    return await service.toggle_todo(db, redis, todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> None:
    """Delete a todo. 404s if not owned by the caller."""
    todo = await _get_owned_todo_or_404(db, todo_id, user.sub)
    await service.delete_todo(db, redis, todo)
