from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.auth.auth import get_current_user
from src.auth.routes import hash_password
from src.db.models import User
from src.db.database import get_db
from src.user.schemas import UserProfile
from typing import Optional

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=list[UserProfile])
async def get_users(
    role: Optional[int] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Не авторизовано")
    
    query = select(User).where(User.is_deleted == False)
    if role:
        query = query.where(User.role_id == role)
    
    query = query.limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return users

@router.put("/users/{user_id}/password", response_model=dict)
async def update_user_password(
    user_id: int,
    new_password: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Не авторизовано")
    
    result = await db.execute(select(User).where(User.user_id == user_id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user.hashed_password = hash_password(new_password)
    await db.commit()
    return {"message": "Пароль обновлен"}

@router.delete("/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Не авторизовано")
    
    result = await db.execute(select(User).where(User.user_id == user_id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user.is_deleted = True
    user.deleted_at = func.now()
    await db.commit()
    return {"message": "Пользователь помечен как удаленный"}