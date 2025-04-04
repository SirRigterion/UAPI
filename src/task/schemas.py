from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from src.db.models import TaskStatus, TaskPriority

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    assignee_id: int

class TaskImageResponse(BaseModel):
    id: int
    image_path: str

    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime]
    author_id: int
    assignee_id: int
    created_at: datetime
    images: List[TaskImageResponse] = []

    class Config:
        from_attributes = True