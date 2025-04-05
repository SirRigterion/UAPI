from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ArticleCreate(BaseModel):
    title: str
    content: str
    image_path: Optional[str] = None

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class ArticleImage(BaseModel):
    id: int
    image_path: str

    class Config:
        from_attributes = True 

class ArticleResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime
    updated_at: datetime
    images: List[ArticleImage]
    is_deleted: bool

    class Config:
        from_attributes = True

class ArticleHistoryResponse(BaseModel):
    id: int
    article_id: int
    user_id: int
    event: str
    changed_at: datetime
    title: str
    content: str
    image_path: Optional[str]
    edited_at: datetime

    class Config:
        from_attributes = True