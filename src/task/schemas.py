from pydantic import BaseModel, validator
from typing import Optional

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "ACTIVE"  # Default to "ACTIVE" as a string
    priority: str = "MEDIUM"  # Default to "MEDIUM" as a string
    due_date: Optional[str] = None
    assignee_id: Optional[int] = None

    @validator("status")
    def validate_status(cls, value):
        valid_statuses = {"ACTIVE", "POSTPONED", "COMPLETED"}
        if value not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return value

    @validator("priority")
    def validate_priority(cls, value):
        valid_priorities = {"LOW", "MEDIUM", "HIGH"}
        if value not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")
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