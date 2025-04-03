from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Схемы для тел запросов ---

class ChatCreate(BaseModel):
    """
    Схема для данных, необходимых для создания нового чата.
    """
    chat_name: str = Field(..., min_length=1, max_length=100, description="Название нового чата")
    member_ids: List[int] = Field([], description="Необязательный список идентификаторов пользователей для приглашения в чат при создании")

class ChatInvite(BaseModel):
    """
    Схема для приглашения пользователя в чат.
    """
    user_id: int = Field(..., description="Идентификатор пользователя, которого нужно пригласить")

class MessageCreate(BaseModel):
    """
    Схема для отправки нового сообщения.
    """
    content: str = Field(..., min_length=1, max_length=2000, description="Содержимое сообщения")

# --- Схемы для тел ответов ---

class ChatInfo(BaseModel):
    """
    Схема, представляющая основную информацию о чате.
    Используется в ответах на создание чата и получение списка чатов.
    """
    chat_id: int = Field(..., description="Уникальный идентификатор чата")
    chat_name: str = Field(..., description="Название чата")
    creator_id: int = Field(..., description="Идентификатор пользователя, создавшего чат")
    # Необязательно: можно добавить количество участников или их список позже
    # member_count: Optional[int] = None

    class Config:
        from_attributes = True  

class ChatListResponse(BaseModel):
    """
    Схема для ответа при получении списка чатов пользователя.
    """
    chats: List[ChatInfo] = Field(..., description="Список чатов, в которых состоит пользователь")

class MessageResponse(BaseModel):
    """
    Схема, представляющая сообщение, отправленное в чате.
    Используется для истории сообщений и вещания сообщений в реальном времени.
    """
    message_id: int = Field(..., description="Уникальный идентификатор сообщения")
    chat_id: int = Field(..., description="Идентификатор чата, к которому относится сообщение")
    user_id: int = Field(..., description="Идентификатор пользователя, отправившего сообщение")
    username: str = Field(..., description="Имя пользователя, отправившего сообщение")
    content: str = Field(..., description="Содержимое сообщения")
    created_at: datetime = Field(..., description="Временная метка создания сообщения")

    class Config:
        from_attributes = True  

class MessageHistoryResponse(BaseModel):
    """
    Схема для ответа при получении истории сообщений чата.
    Включает детали пагинации.
    """
    messages: List[MessageResponse] = Field(..., description="Список полученных сообщений, обычно от старых к новым в списке")
    total_messages: int = Field(..., description="Общее количество сообщений в чате")
    skip: int = Field(..., description="Количество пропущенных сообщений (смещение)")
    limit: int = Field(..., description="Максимальное количество сообщений, возвращенных в этом ответе")

    class Config:
        from_attributes = True  