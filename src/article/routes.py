from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from src.auth.auth import get_current_user
from src.db.models import User, Article, ArticleHistory
from src.db.database import get_db
from src.article.schemas import ArticleCreate, ArticleUpdate, ArticleResponse, ArticleHistoryResponse
from datetime import datetime, timedelta

router = APIRouter(prefix="/articles", tags=["articles"])

@router.get("/", response_model=list[ArticleResponse])
async def get_articles(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Article).where(Article.is_deleted == False))
    articles = result.scalars().all()
    return articles

@router.post("/", response_model=ArticleResponse)
async def create_article(
    article_data: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = Article(
        title=article_data.title,
        content=article_data.content,
        image_path=article_data.image_path,
        author_id=current_user.user_id
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article

@router.put("/{id}", response_model=ArticleResponse)
async def update_article(
    id: int,
    article_data: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Article).where(Article.id == id, Article.is_deleted == False))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Сохраняем историю изменений
    history = ArticleHistory(
        article_id=article.id,
        editor_id=current_user.user_id,
        title=article.title,
        content=article.content,
        image_path=article.image_path
    )
    db.add(history)

    # Обновляем статью
    if article_data.title:
        article.title = article_data.title
    if article_data.content:
        article.content = article_data.content
    if article_data.image_path is not None:
        article.image_path = article_data.image_path

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
            Article.is_deleted == True,
            Article.updated_at > datetime.utcnow() - timedelta(days=7)
        )
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found or cannot be restored")
    if article.author_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized")

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
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != current_user.user_id and current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(ArticleHistory).where(ArticleHistory.article_id == id))
    history = result.scalars().all()
    return history