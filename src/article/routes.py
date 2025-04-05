import os
from typing import List, Optional
import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.auth.auth import get_current_user
from src.db.models import User, Article, ArticleHistory, ArticleImage
from src.db.database import get_db
from src.core.config import settings
from src.article.schemas import ArticleResponse, ArticleHistoryResponse
from datetime import datetime

router = APIRouter(prefix="/articles", tags=["articles"])

@router.get("/", response_model=List[ArticleResponse])
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
    articles = result.scalars().all()
    return articles

@router.post("/", response_model=ArticleResponse)
async def create_article(
    title: str = Form(...),
    content: str = Form(...),
    images: List[UploadFile] = File([]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create article
    article = Article(title=title, content=content, author_id=current_user.user_id)
    db.add(article)
    await db.commit()
    await db.refresh(article)

    # Save images
    for image in images:
        file_path = f"{settings.UPLOAD_DIR}/article_{article.id}_{image.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure directory exists
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await image.read()
            await out_file.write(content)

        db.add(ArticleImage(article_id=article.id, image_path=file_path))

    await db.commit()
    await db.refresh(article)
    return article

@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    images: List[UploadFile] = File([]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Article)
        .where(Article.id == article_id)
        .options(selectinload(Article.images))
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if article.author_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Create history entry before updating
    history_entry = ArticleHistory(
        article_id=article.id,
        user_id=current_user.user_id,
        event="update",
        changed_title=article.title,
        changed_content=article.content,
    )
    db.add(history_entry)

    # Update article fields
    if title is not None:
        article.title = title
    if content is not None:
        article.content = content
    article.updated_at = datetime.utcnow()

    # Remove existing images
    if article.images:
        for image in article.images:
            # Delete physical file
            try:
                if os.path.exists(image.image_path):
                    os.remove(image.image_path)
            except Exception as e:
                print(f"Error deleting image file: {e}")
            # Remove database record
            await db.delete(image)

    # Add new images
    for image in images:
        file_path = f"{settings.UPLOAD_DIR}/article_{article.id}_{image.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
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
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized")

    article.is_deleted = True
    article.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "Article marked as deleted"}

@router.post("/{id}/restore", response_model=ArticleResponse)
async def restore_article(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Article).where(
            Article.id == id,
            Article.is_deleted == True
        )
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found or cannot be restored")
    if article.author_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized")

    article.is_deleted = False
    article.deleted_at = None
    await db.commit()
    await db.refresh(article)
    return article

@router.get("/{id}/history", response_model=List[ArticleHistoryResponse])
async def get_article_history(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Article)
        .where(Article.id == id, Article.is_deleted == False)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if article.author_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(ArticleHistory)
        .where(ArticleHistory.article_id == id)
        .order_by(ArticleHistory.changed_at.desc())
    )
    history = result.scalars().all()
    
    return history