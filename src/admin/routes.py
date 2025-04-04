from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.auth.auth import get_current_user
from src.db.models import User, Role
from src.db.database import get_db
from src.user.schemas import UserProfile
from datetime import datetime
import bcrypt

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=list[UserProfile])
async def get_users(
    role: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role_id != 2:  # Только админ
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = select(User).where(User.is_deleted == False)
    if role:
        result = await db.execute(select(Role).where(Role.role_name == role))
        role_obj = result.scalar_one_or_none()
        if role_obj:
            query = query.where(User.role_id == role_obj.role_id)
    
    result = await db.execute(query)
    users = result.scalars().all()
    return users

@router.delete("/users/{id}", response_model=dict)
async def delete_user(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(select(User).where(User.user_id == id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "User marked as deleted"}

@router.put("/users/{id}/password", response_model=dict)
async def change_user_password(
    id: int,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(select(User).where(User.user_id == id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    await db.commit()
    return {"message": "Password updated"}