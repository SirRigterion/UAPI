from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.database import get_db
from src.auth.schemas import UserCreate, UserLogin
from src.user.schemas import UserProfile
from src.db.models import User
from src.auth.auth import create_access_token, set_auth_cookie, get_current_user
import bcrypt

router = APIRouter(prefix="/auth", tags=["auth"])

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

@router.post("/register", response_model=UserProfile)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where((User.email == user.email) | (User.username == user.username))
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email or username already registered")
    
    hashed_password = hash_password(user.password)
    new_user = User(
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    token = create_access_token(data={"sub": user.email})
    response = Response(status_code=201)
    set_auth_cookie(response, token)
    return new_user

@router.post("/login", response_model=dict)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalar_one_or_none()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": user.email})
    response = Response(status_code=200)
    set_auth_cookie(response, token)
    return {"message": "Logged in successfully", "status": "success"}

@router.post("/logout", response_model=dict)
async def logout():
    response = Response(status_code=200)
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}