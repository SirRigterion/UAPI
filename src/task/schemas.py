from pydantic import BaseModel, validator
from typing import Optional

class TaskCreate(BaseModel):
    status: str = "ACTIVE"
    priority: str = "MEDIUM"
    
    @validator("status")
    def validate_status(cls, value):
        valid_statuses = {"ACTIVE", "POSTPONED", "COMPLETED"}
        if value not in valid_statuses:
            raise ValueError(f"Invalid status: {value}")
        return value
    
    @validator("priority")
    def validate_priority(cls, value):
        valid_priorities = {"LOW", "MEDIUM", "HIGH"}
        if value not in valid_priorities:
            raise ValueError(f"Invalid priority: {value}")
        return value

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[str]
    author_id: int
    assignee_id: Optional[int]
    created_at: str
    is_deleted: bool

    class Config:
        from_attributes = True

class TaskImageResponse(BaseModel):
    id: int
    image_path: str

    class Config:
        from_attributes = True