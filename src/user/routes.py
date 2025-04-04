from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.database import get_db
from src.auth.auth import get_current_user
from src.db.models import User
from src.user.schemas import UserProfile, UserUpdate
import aiofiles
import os
from src.core.config import settings

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=dict)
async def update_profile(
    user_update: UserUpdate = Depends(),
    photo: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user_update.username and user_update.username != current_user.username:
        result = await db.execute(
            select(User).where(User.username == user_update.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Имя пользователя уже занято")
        current_user.username = user_update.username

    if photo:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = f"{settings.UPLOAD_DIR}/{current_user.user_id}_{photo.filename}"
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await photo.read()
            await out_file.write(content)
        current_user.avatar = file_path
    
    await db.commit()
    await db.refresh(current_user)
    return {"message": "Профиль обновлен"}

@router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.user_id == user_id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.get("/search", response_model=list[UserProfile])
async def search_users(
    username: Optional[str] = None,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    role_id: Optional[int] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ограничение только для администраторов, если нужно
    # if current_user.role_id != 2:
    #     raise HTTPException(status_code=403, detail="Not authorized")

    query = select(User).where(User.is_deleted == False)
    if username:
        query = query.where(User.username.ilike(f"%{username}%"))
    if full_name:
        query = query.where(User.full_name.ilike(f"%{full_name}%"))
    if email:
        query = query.where(User.email.ilike(f"%{email}%"))
    if role_id:
        query = query.where(User.role_id == role_id)
    
    query = query.limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return users