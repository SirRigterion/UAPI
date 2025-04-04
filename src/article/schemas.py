from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ArticleCreate(BaseModel):
    title: str
    content: str
    image_path: Optional[str] = None

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_path: Optional[str] = None

class ArticleResponse(BaseModel):
    id: int
    title: str
    content: str
    image_path: Optional[str]
    author_id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class ArticleImage(BaseModel):
    id: int
    article_id: int
    image_path: str

class ArticleHistoryResponse(BaseModel):
    id: int
    article_id: int
    editor_id: int
    title: str
    content: str
    image_path: Optional[str]
    edited_at: datetime

    class Config:
        from_attributes = True