from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from src.auth.auth import get_current_user
from src.db.models import User, Task, TaskStatus
from src.db.database import get_db
from src.task.schemas import TaskCreate, TaskUpdateStatus, TaskResponse
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=list[TaskResponse])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    title: Optional[str] = None,
    due_date: Optional[datetime] = None,
    assignee_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Task)
    if status:
        query = query.where(Task.status == status)
    if title:
        query = query.where(Task.title.ilike(f"%{title}%"))
    if due_date:
        query = query.where(Task.due_date == due_date)
    if assignee_id:
        query = query.where(Task.assignee_id == assignee_id)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    return tasks

@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.user_id == task_data.assignee_id, User.is_deleted == False))
    assignee = result.scalar_one_or_none()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")

    task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        due_date=task_data.due_date,
        author_id=current_user.user_id,
        assignee_id=task_data.assignee_id
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

@router.put("/{id}/status", response_model=TaskResponse)
async def update_task_status(
    id: int,
    status_data: TaskUpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Task).where(Task.id == id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.author_id != current_user.user_id and task.assignee_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized")

    task.status = status_data.status
    await db.commit()
    await db.refresh(task)
    return task