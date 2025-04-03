from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from src.db.database import Base

class Role(Base):
    __tablename__ = "roles"
    
    role_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Связь с пользователями (обратная)
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"), default=1, nullable=False)
    registered_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Связи
    role = relationship("Role", back_populates="users")
    created_chats = relationship("Chat", back_populates="creator")
    chat_memberships = relationship("ChatMember", back_populates="user")
    messages = relationship("Message", back_populates="user")

class Chat(Base):
    __tablename__ = "chats"
    
    chat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_name: Mapped[str] = mapped_column(String(100), nullable=False)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)

    # Связи
    creator = relationship("User", back_populates="created_chats")
    members = relationship("ChatMember", back_populates="chat")
    messages = relationship("Message", back_populates="chat")

class ChatMember(Base):
    __tablename__ = "chat_members"
    
    chatmember_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.chat_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    
    # Уникальное ограничение
    __table_args__ = (UniqueConstraint('chat_id', 'user_id', name='unique_chat_member'),)

    # Связи
    chat = relationship("Chat", back_populates="members")
    user = relationship("User", back_populates="chat_memberships")

class Message(Base):
    __tablename__ = "messages"
    
    message_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.chat_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Связи
    chat = relationship("Chat", back_populates="messages")
    user = relationship("User", back_populates="messages")