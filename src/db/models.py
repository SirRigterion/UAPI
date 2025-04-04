from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Boolean, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from src.db.database import Base
from enum import Enum

class Role(Base):
    __tablename__ = "roles"
    
    role_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"), default=1)
    registered_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    
    role = relationship("Role")

class Chat(Base):
    __tablename__ = "chats"
    
    chat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_name: Mapped[str] = mapped_column(String(100), nullable=False)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))

class ChatMember(Base):
    __tablename__ = "chat_members"
    
    chatmember_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.chat_id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    
    __table_args__ = (UniqueConstraint('chat_id', 'user_id', name='unique_chat_member'),)

class Message(Base):
    __tablename__ = "messages"
    
    message_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.chat_id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())

class Article(Base):
    __tablename__ = "articles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String(5000), nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now(), onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    author = relationship("User")
    history = relationship("ArticleHistory")

class ArticleHistory(Base):
    __tablename__ = "article_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))
    editor_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String(5000), nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=True)
    edited_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    
    editor = relationship("User")

class TaskStatus(str, Enum):
    ACTIVE = "Текущие"
    POSTPONED = "Отложенные"
    COMPLETED = "Выполненные"

class TaskPriority(str, Enum):
    LOW = "Низкий"
    MEDIUM = "Средний"
    HIGH = "Высокий"

class Task(Base):
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.ACTIVE)
    priority: Mapped[TaskPriority] = mapped_column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    due_date: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    
    author = relationship("User", foreign_keys=[author_id])
    assignee = relationship("User", foreign_keys=[assignee_id])