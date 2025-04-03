from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.auth.auth import get_current_user
from src.db.models import User, Chat, ChatMember, Message
from src.db.database import get_db, get_redis
from src.chat.schemas import ChatCreate, ChatInfo, ChatInvite, ChatListResponse, MessageCreate, MessageResponse, MessageHistoryResponse
from typing import List, Dict
from sqlalchemy.orm import joinedload
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["чат"])

# Хранилище активных WebSocket-соединений
connected_clients: Dict[int, List[WebSocket]] = {}

# Создание чата
@router.post("/create", response_model=dict)
async def create_chat(
    chat_data: ChatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chat = Chat(chat_name=chat_data.chat_name, creator_id=current_user.user_id)
    db.add(chat)
    await db.flush()

    db.add(ChatMember(chat_id=chat.chat_id, user_id=current_user.user_id))
    for member_id in chat_data.member_ids:
        if member_id != current_user.user_id:
            result = await db.execute(select(User).where(User.user_id == member_id))
            if result.scalar_one_or_none():
                db.add(ChatMember(chat_id=chat.chat_id, user_id=member_id))

    await db.commit()
    return {"chat_id": chat.chat_id, "сообщение": "Чат успешно создан"}

# Приглашение пользователя в чат
@router.post("/{chat_id}/invite", response_model=dict)
async def invite_to_chat(
    chat_id: int,
    invite: ChatInvite,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Chat).where(Chat.chat_id == chat_id, Chat.creator_id == current_user.user_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=403, detail="Чат не найден или вы не являетесь создателем")

    result = await db.execute(select(User).where(User.user_id == invite.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    result = await db.execute(
        select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == invite.user_id)
    )
    existing_member = result.scalar_one_or_none()
    if existing_member:
        raise HTTPException(status_code=400, detail="Пользователь уже является участником")

    db.add(ChatMember(chat_id=chat_id, user_id=invite.user_id))
    await db.commit()
    return {"сообщение": f"Пользователь {user.username} приглашен в чат {chat_id}"}

# Отправка сообщения через HTTP (с уведомлением через WebSocket)
@router.post("/{chat_id}/send", response_model=MessageResponse)
async def send_message(
    chat_id: int,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == current_user.user_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Вы не являетесь участником этого чата")

    message = Message(chat_id=chat_id, user_id=current_user.user_id, content=message_data.content)
    db.add(message)
    await db.commit()
    await db.refresh(message)

    msg_response = MessageResponse(
        message_id=message.message_id,
        chat_id=chat_id,
        user_id=current_user.user_id,
        username=current_user.username,
        content=message_data.content,
        created_at=message.created_at
    )
    msg_json = msg_response.model_dump_json()

    # Проверка доступности Redis
    redis_client = await get_redis()
    if redis_client:
        try:
            await redis_client.lpush(f"chat:{chat_id}", msg_json)
            await redis_client.ltrim(f"chat:{chat_id}", 0, 99)
        except Exception as e:
            logger.error(f"Ошибка при работе с Redis: {e}")
    else:
        logger.warning("Redis недоступен, сообщение не сохранено в кэше")

    if chat_id in connected_clients:
        for client in connected_clients[chat_id]:
            await client.send_text(msg_json)

    return msg_response

# WebSocket для чата
@router.websocket("/{chat_id}")
async def websocket_chat(
    websocket: WebSocket,
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == current_user.user_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        await websocket.close(code=1008, reason="Вы не участник чата")
        return

    await websocket.accept()

    if chat_id not in connected_clients:
        connected_clients[chat_id] = []
    connected_clients[chat_id].append(websocket)

    try:
        # Проверка кэша в Redis
        redis_client = await get_redis()
        if redis_client:
            try:
                cached_messages = await redis_client.lrange(f"chat:{chat_id}", 0, 9)
                for msg in reversed(cached_messages):
                    await websocket.send_text(msg)
            except Exception as e:
                logger.error(f"Ошибка при чтении из Redis: {e}")
        else:
            logger.warning("Redis недоступен, кэш сообщений не загружен")

        while True:
            data = await websocket.receive_text()
            message = Message(chat_id=chat_id, user_id=current_user.user_id, content=data)
            db.add(message)
            await db.commit()
            await db.refresh(message)

            msg_response = MessageResponse(
                message_id=message.message_id,
                chat_id=chat_id,
                user_id=current_user.user_id,
                username=current_user.username,
                content=data,
                created_at=message.created_at
            )
            msg_json = msg_response.model_dump_json()

            if redis_client:
                try:
                    await redis_client.lpush(f"chat:{chat_id}", msg_json)
                    await redis_client.ltrim(f"chat:{chat_id}", 0, 99)
                except Exception as e:
                    logger.error(f"Ошибка при записи в Redis: {e}")

            for client in connected_clients[chat_id]:
                await client.send_text(msg_json)

    except WebSocketDisconnect:
        connected_clients[chat_id].remove(websocket)
        if not connected_clients[chat_id]:
            del connected_clients[chat_id]
    except Exception as e:
        await websocket.close(code=1011, reason=f"Ошибка: {str(e)}")
        connected_clients[chat_id].remove(websocket)
        if not connected_clients[chat_id]:
            del connected_clients[chat_id]

# Получение списка чатов пользователя
@router.get("/list", response_model=ChatListResponse)
async def list_user_chats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Chat)
        .join(ChatMember, Chat.chat_id == ChatMember.chat_id)
        .where(ChatMember.user_id == current_user.user_id)
        .order_by(Chat.chat_name)
    )
    chats = result.scalars().unique().all()

    chat_infos = [
        ChatInfo(
            chat_id=chat.chat_id,
            chat_name=chat.chat_name,
            creator_id=chat.creator_id,
        ) for chat in chats
    ]

    return ChatListResponse(chats=chat_infos)

# Получение истории сообщений чата
@router.get("/{chat_id}/history", response_model=MessageHistoryResponse)
async def get_chat_history(
    chat_id: int,
    skip: int = Query(0, ge=0, description="Количество сообщений для пропуска"),
    limit: int = Query(50, ge=1, le=200, description="Максимальное количество возвращаемых сообщений"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == current_user.user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Вы не являетесь участником этого чата")

    result = await db.execute(
        select(Message)
        .options(joinedload(Message.user))
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()

    message_responses = [
        MessageResponse(
            message_id=msg.message_id,
            chat_id=msg.chat_id,
            user_id=msg.user_id,
            username=msg.user.username if msg.user else "Неизвестный пользователь",
            content=msg.content,
            created_at=msg.created_at
        ) for msg in messages
    ]

    count_result = await db.execute(
        select(func.count(Message.message_id)).where(Message.chat_id == chat_id)
    )
    total_messages = count_result.scalar_one()

    return MessageHistoryResponse(
        messages=list(reversed(message_responses)),
        total_messages=total_messages,
        skip=skip,
        limit=limit
    )