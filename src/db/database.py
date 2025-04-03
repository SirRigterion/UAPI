from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import text
from src.core.config import settings
import redis.asyncio as redis
import logging
from typing import AsyncGenerator
import asyncio

logger = logging.getLogger(__name__)

# Создаем асинхронный движок для PostgreSQL
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Создаем фабрику сессий
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Redis клиент (инициализируем как None, чтобы проверить подключение позже)
redis_client = None

async def init_redis() -> redis.Redis | None:
    """Инициализация подключения к Redis с обработкой ошибок."""
    global redis_client
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        # Проверка подключения с тайм-аутом
        await asyncio.wait_for(redis_client.ping(), timeout=5.0)
        logger.info("Подключение к Redis успешно")
        return redis_client
    except (redis.ConnectionError, asyncio.TimeoutError) as e:
        logger.error(f"Не удалось подключиться к Redis: {e}")
        redis_client = None  # Устанавливаем None, если подключение не удалось
        return None
    except Exception as e:
        logger.error(f"Неизвестная ошибка при подключении к Redis: {e}")
        redis_client = None
        return None

async def get_redis() -> redis.Redis | None:
    """Получение клиента Redis с проверкой его доступности."""
    if redis_client is None:
        logger.warning("Redis недоступен, попытка повторного подключения")
        await init_redis()
    return redis_client

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Получение сессии базы данных."""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Ошибка в сессии базы данных: {e}")
            raise

async def test_db_connection() -> None:
    """Проверка подключения к базе данных."""
    try:
        async with engine.connect() as conn:
            # Используем text() для raw SQL-запроса
            result = await conn.scalar(text("SELECT 1"))
            if result != 1:
                raise ValueError("Неожиданный результат тестового запроса к базе данных")
        logger.info("Подключение к базе данных успешно")
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        raise

async def startup() -> None:
    """Инициализация при запуске приложения."""
    await test_db_connection()
    await init_redis()

# Пример использования в коде FastAPI (добавьте это в основной файл приложения)
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await startup()