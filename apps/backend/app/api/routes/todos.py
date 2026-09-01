import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.db import get_db
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoRead

router = APIRouter(prefix="/api/v1/todos", tags=["todos"])


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
async def create_todo(
    payload: TodoCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Todo:
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
    result = await db.execute(
        select(Todo).where(Todo.owner_id == user.sub).order_by(Todo.created_at.desc())
    )
    return list(result.scalars().all())


async def _get_owned_todo(db: AsyncSession, todo_id: uuid.UUID, owner_id: str) -> Todo:
    result = await db.execute(
        select(Todo).where(Todo.id == todo_id, Todo.owner_id == owner_id)
    )
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
    todo = await _get_owned_todo(db, todo_id, user.sub)
    await db.delete(todo)
    await db.commit()
