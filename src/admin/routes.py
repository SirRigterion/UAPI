from fastapi import APIRouter, Depends, Form, HTTPException, Query
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

@router.put("/users/{user_id}", response_model=UserProfile)
async def update_user(
    user_id: int,
    username: Optional[str] = Form(None),
    full_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    avatar: Optional[str] = Form(None),
    role_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Проверка прав доступа (только админ)
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Не авторизовано")
    
    # Получаем пользователя для редактирования
    result = await db.execute(
        select(User)
        .where(User.user_id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Запрещаем редактирование других админов
    if user.role_id == 2 and user.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Нельзя редактировать других администраторов")
    
    # Обновляем поля, если они переданы
    if username is not None:
        # Проверяем уникальность username
        existing_user = await db.execute(
            select(User)
            .where(User.username == username, User.user_id != user_id)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Имя пользователя уже занято")
        user.username = username
    
    if full_name is not None:
        user.full_name = full_name
    
    if email is not None:
        # Проверяем уникальность email
        existing_email = await db.execute(
            select(User)
            .where(User.email == email, User.user_id != user_id)
        )
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email уже используется")
        user.email = email
    
    if avatar is not None:
        user.avatar = avatar
    
    if role_id is not None:
        if role_id == 2:
            raise HTTPException(status_code=403, detail="Нельзя назначать роль администратора через этот эндпоинт")
        user.role_id = role_id
    
    await db.commit()
    await db.refresh(user)
    return user

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