from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from src.db.database import Base
from datetime import datetime

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

class Role(Base):
    __tablename__ = "roles"
    role_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(String(50), nullable=False)

class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(String(5000), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    images = relationship("ArticleImage", back_populates="article") 

class ArticleImage(Base):
    __tablename__ = "article_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    article = relationship("Article", back_populates="images")

class ArticleHistory(Base):
    __tablename__ = "article_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    event: Mapped[str] = mapped_column(String(50))
    changed_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())