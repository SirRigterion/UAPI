from fastapi import FastAPI
from src.auth.routes import router as auth_router
from src.user.routes import router as user_router
from src.chat.routes import router as chat_router
from src.db.database import Base, engine, startup as db_startup
from src.db.models import Role
from sqlalchemy.future import select
import logging
import asyncio

logger = logging.getLogger(__name__)

app = FastAPI(title="API Чата", description="API для управления пользователями и чатами")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(chat_router)

async def wait_for_db(max_attempts=10, delay=2):
    """Ожидание готовности базы данных с повторными попытками."""
    attempt = 1
    while attempt <= max_attempts:
        try:
            async with engine.connect() as conn:
                await conn.execute(select(1))
            logger.info("База данных доступна")
            return
        except Exception as e:
            logger.warning(f"Попытка {attempt}/{max_attempts} подключения к базе данных не удалась: {e}")
            if attempt == max_attempts:
                raise Exception("Не удалось подключиться к базе данных после всех попыток")
            await asyncio.sleep(delay)
        attempt += 1

@app.on_event("startup")
async def startup():
    """Инициализация приложения при запуске."""
    try:
        await wait_for_db()  # Ожидание базы данных
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with engine.connect() as conn:
            result = await conn.execute(select(Role))
            roles = result.fetchall()
            if not roles:
                await conn.execute(
                    Role.__table__.insert().values([
                        {"role_id": 1, "role_name": "пользователь"},
                        {"role_id": 2, "role_name": "администратор"}
                    ])
                )
                await conn.commit()
                logger.info("Роли по умолчанию успешно созданы")
        
        await db_startup()
        logger.info("Приложение успешно запущено")
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """Очистка ресурсов при завершении работы приложения."""
    try:
        await engine.dispose()
        logger.info("Соединение с базой данных закрыто")
    except Exception as e:
        logger.error(f"Ошибка при завершении работы приложения: {e}")
        raise