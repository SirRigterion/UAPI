from pydantic import BaseModel, validator, EmailStr
import re

class UserCreate(BaseModel):
    username: str  # Логин
    full_name: str  # ФИО
    email: EmailStr
    password: str

    @validator('username')
    def validate_username(cls, value):
        if not re.match(r'^[a-zA-Z]+$', value):
            raise ValueError('Username must contain only Latin letters')
        return value

    @validator('full_name')
    def validate_full_name(cls, value):
        if not re.match(r'^[а-яА-ЯёЁ\s]+$', value):
            raise ValueError('Full name must contain only Russian letters and spaces')
        return value

    @validator('password')
    def validate_password(cls, value):
        if not re.match(r'^[a-zA-Z0-9!@#$%^&*]+$', value):
            raise ValueError('Password must contain only Latin letters, numbers, and symbols (!@#$%^&*)')
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return value

class UserLogin(BaseModel):
    email: EmailStr
    password: str