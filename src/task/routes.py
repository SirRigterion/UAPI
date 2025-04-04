from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from src.auth.auth import get_current_user
from src.db.models import TaskPriority, User, Task, TaskImage, TaskHistory
from src.db.database import get_db
from src.task.schemas import TaskCreate, TaskResponse, TaskStatus
from typing import Optional, List
import aiofiles
from src.core.config import settings
import os

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    # Удаляем проверки статуса и приоритета через таблицы
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,  # Используем строку напрямую
        priority=task.priority,  # Используем строку напрямую
        due_date=task.due_date,
        author_id=1,
        assignee_id=task.assignee_id
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    title: Optional[str] = None,
    assignee_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Task).where(Task.is_deleted == False)
    if title:
        query = query.where(Task.title.ilike(f"%{title}%"))
    if assignee_id:
        query = query.where(Task.assignee_id == assignee_id)
    if status:
        query = query.where(Task.status == status)
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.put("/{id}", response_model=TaskResponse)
async def update_task(
    id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    priority: Optional[TaskPriority] = Form(None),
    due_date: Optional[datetime] = Form(None),
    assignee_id: Optional[int] = Form(None),
    images: List[UploadFile] = File([]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Task).where(Task.id == id, Task.is_deleted == False))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.author_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized")

    if title:
        task.title = title
    if description:
        task.description = description
    if priority:
        task.priority = priority
    if due_date:
        task.due_date = due_date.replace(tzinfo=None)
    if assignee_id:
        result = await db.execute(select(User).where(User.user_id == assignee_id, User.is_deleted == False))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Assignee not found")
        task.assignee_id = assignee_id

    db.add(TaskHistory(task_id=task.id, user_id=current_user.user_id, event="update"))
    
    for image in images:
        file_path = f"{settings.UPLOAD_DIR}/task_{task.id}_{image.filename}"
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await image.read()
            await out_file.write(content)
        db.add(TaskImage(task_id=task.id, image_path=file_path))
        db.add(TaskHistory(task_id=task.id, user_id=current_user.user_id, event="image_create"))
    
    await db.commit()
    await db.refresh(task)
    return task

@router.put("/{id}/status", response_model=TaskResponse)
async def update_task_status(
    id: int,
    status: str,  # Меняем тип на str
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Добавляем валидацию статуса
    valid_statuses = {"ACTIVE", "POSTPONED", "COMPLETED"}
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.execute(select(Task).where(Task.id == id, Task.is_deleted == False))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if status == TaskStatus.POSTPONED and task.status != TaskStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Can only postpone from ACTIVE")
    if status == TaskStatus.COMPLETED and task.status not in [TaskStatus.ACTIVE, TaskStatus.POSTPONED]:
        raise HTTPException(status_code=400, detail="Can only complete from ACTIVE or POSTPONED")
    if status == TaskStatus.ACTIVE and task.status not in [TaskStatus.POSTPONED, TaskStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="Can only return to work from POSTPONED or COMPLETED")
    
    task.status = status
    db.add(TaskHistory(task_id=id, user_id=current_user.user_id, event="status_update"))
    await db.commit()
    await db.refresh(task)
    return task

@router.get("/counts", response_model=dict)
async def get_task_counts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Task.status, func.count()).where(Task.is_deleted == False).group_by(Task.status))
    counts = {row[0]: row[1] for row in result.all()}
    return {
        "current": counts.get("ACTIVE", 0),
        "postponed": counts.get("POSTPONED", 0),
        "completed": counts.get("COMPLETED", 0)
    }
