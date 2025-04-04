from typing import List, Optional
import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.auth.auth import get_current_user
from src.db.models import User, Article, ArticleHistory
from src.db.database import get_db
from src.core.config import settings
from src.article.schemas import ArticleImage, ArticleResponse, ArticleHistoryResponse
from datetime import datetime, timedelta

router = APIRouter(prefix="/articles", tags=["articles"])

@router.get("/", response_model=list[ArticleResponse])
async def get_articles(
    title: Optional[str] = None,
    author_id: Optional[int] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Article).where(Article.is_deleted == False)
    if title:
        query = query.where(Article.title.ilike(f"%{title}%"))
    if author_id:
        query = query.where(Article.author_id == author_id)
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=ArticleResponse)
async def create_article(
    title: str = Form(...),
    content: str = Form(...),
    images: List[UploadFile] = File([]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Создаем статью
    article = Article(title=title, content=content, author_id=current_user.user_id)
    db.add(article)
    await db.commit()
    await db.refresh(article)

    for image in images:
        file_path = f"{settings.UPLOAD_DIR}/article_{article.id}_{image.filename}"
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await image.read()
            await out_file.write(content)
        
        db.add(ArticleImage(article_id=article.id, image_path=file_path))
    
    await db.commit()
    await db.refresh(article)
    
    return article

@router.put("/{id}", response_model=ArticleResponse)
async def update_article(
    id: int,
    title: str = Form(None),
    content: str = Form(None),
    images: List[UploadFile] = File([]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Article).where(Article.id == id, Article.is_deleted == False))
    article = result.scalar_one_or_none()
    if not article or article.author_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if title:
        article.title = title
    if content:
        article.content = content
    for image in images:
        file_path = f"{settings.UPLOAD_DIR}/article_{article.id}_{image.filename}"
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await image.read()
            await out_file.write(content)
        db.add(ArticleImage(article_id=article.id, image_path=file_path))
    await db.commit()
    await db.refresh(article)
    return article

@router.delete("/{id}", response_model=dict)
async def delete_article(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Article).where(Article.id == id, Article.is_deleted == False))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    if article.author_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Не авторизовано")

    article.is_deleted = True
    await db.commit()
    return {"message": "Статья отмечена как удаленная"}

@router.post("/{id}/restore", response_model=ArticleResponse)
async def restore_article(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Article).where(
            Article.id == id,
            Article.is_deleted == True,
            Article.updated_at > datetime.utcnow() - timedelta(days=7)
        )
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена or cannot be restored")
    if article.author_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Не авторизовано")

    article.is_deleted = False
    await db.commit()
    await db.refresh(article)
    return article

@router.get("/{id}/history", response_model=list[ArticleHistoryResponse])
async def get_article_history(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Article).where(Article.id == id, Article.is_deleted == False))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    if article.author_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Не авторизовано")

    result = await db.execute(select(ArticleHistory).where(ArticleHistory.article_id == id))
    history = result.scalars().all()
    return history