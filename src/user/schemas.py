from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

class UserProfile(BaseModel):
    user_id: int
    username: str
    full_name: str
    email: str
    avatar: Optional[str] = None
    role_id: int
    registered_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None

class UserSearch(BaseModel):
    filters: Dict[str, str]  # Например, {"username": "john", "full_name": "Иван"}
    limit: int = 10  # Максимальное количество возвращаемых пользователей