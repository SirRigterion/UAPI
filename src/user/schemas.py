from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserProfile(BaseModel):
    user_id: int
    username: str
    email: str
    avatar: Optional[str] = None
    role_id: int
    registered_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None