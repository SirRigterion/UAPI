from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.database import get_db
from src.auth.auth import get_current_user
from src.db.models import User
from src.user.schemas import UserProfile, UserUpdate
import aiofiles
import os
from src.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["пользователь"])

@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Получение профиля текущего пользователя."""
    try:
        logger.info(f"Профиль пользователя {current_user.username} успешно получен")
        return current_user
    except Exception as e:
        logger.error(f"Ошибка при получении профиля пользователя {current_user.username}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера при получении профиля")

@router.put("/profile", response_model=dict)
async def update_profile(
    user_update: UserUpdate = Depends(),
    photo: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление профиля пользователя."""
    try:
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
        logger.info(f"Профиль пользователя {current_user.username} успешно обновлен")
        return {"сообщение": "Профиль успешно обновлен"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Ошибка при обновлении профиля пользователя {current_user.username}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера при обновлении профиля")

@router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение профиля пользователя по ID."""
    try:
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        logger.info(f"Профиль пользователя с ID {user_id} успешно получен")
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Ошибка при получении профиля пользователя с ID {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера при получении профиля")
    
