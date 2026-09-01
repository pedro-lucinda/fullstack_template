import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.constants import API_V1_PREFIX
from app.core.db import get_db
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoRead

router = APIRouter(prefix=f"{API_V1_PREFIX}/todos", tags=["todos"])


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
async def create_todo(
    payload: TodoCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Todo:
    """Create a new todo owned by the authenticated user."""
    todo = Todo(owner_id=user.sub, title=payload.title)
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    return todo


@router.get("", response_model=list[TodoRead])
async def list_todos(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[Todo]:
    """List the authenticated user's todos, newest first."""
    result = await db.execute(
        select(Todo).where(Todo.owner_id == user.sub).order_by(Todo.created_at.desc())
    )
    return list(result.scalars().all())


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
) -> Todo:
    """Flip a todo's `completed` flag. 404s if not owned by the caller."""
    todo = await _get_owned_todo(db, todo_id, user.sub)
    todo.completed = not todo.completed
    await db.commit()
    await db.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> None:
    """Delete a todo. 404s if not owned by the caller."""
    todo = await _get_owned_todo(db, todo_id, user.sub)
    await db.delete(todo)
    await db.commit()
