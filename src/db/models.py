from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from src.db.database import Base
from datetime import datetime

# Статусы задач (таблица)
class TaskStatus(Base):
    __tablename__ = "task_statuses"
    status_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

# Приоритеты задач (таблица)
class TaskPriority(Base):
    __tablename__ = "task_priorities"
    priority_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    priority_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

# Пользователи
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

# Роли
class Role(Base):
    __tablename__ = "roles"
    role_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(String(50), nullable=False)

# Статьи
class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(String(5000), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    images = relationship("ArticleImage", back_populates="article", lazy="selectin")

# Изображения статей
class ArticleImage(Base):
    __tablename__ = "article_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    article = relationship("Article", back_populates="images")

# История статей
class ArticleHistory(Base):
    __tablename__ = "article_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    event: Mapped[str] = mapped_column(String(50))  # "create", "update", "delete", "image_create", "image_delete"
    changed_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())

# Задачи
class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(5000), nullable=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("task_statuses.status_id"), default=1, nullable=False)
    priority_id: Mapped[int] = mapped_column(ForeignKey("task_priorities.priority_id"), default=2, nullable=False)
    due_date: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    status = relationship("TaskStatus")
    priority = relationship("TaskPriority")
    images = relationship("TaskImage", back_populates="task")

# Изображения задач
class TaskImage(Base):
    __tablename__ = "task_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    task = relationship("Task", back_populates="images")

# История задач
class TaskHistory(Base):
    __tablename__ = "task_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    event: Mapped[str] = mapped_column(String(50))  # "create", "update", "delete", "image_create", "image_delete"
    changed_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())

# Чаты
class Chat(Base):
    __tablename__ = "chats"
    chat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())

# Участники чата
class ChatMember(Base):
    __tablename__ = "chat_members"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.chat_id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    joined_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())

# Сообщения
class Message(Base):
    __tablename__ = "messages"
    message_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.chat_id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    user = relationship("User")