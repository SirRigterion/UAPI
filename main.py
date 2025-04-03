from fastapi import FastAPI
from src.auth.routes import router as auth_router
from src.user.routes import router as user_router
from src.chat.routes import router as chat_router
from src.db.database import Base, engine, startup as db_startup
from src.db.models import Role
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="UAPI", description="API для управления пользователями и чатами")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(chat_router)

@app.on_event("startup")
async def startup():
    """Инициализация приложения при запуске."""
    try:
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
        
        # Инициализация базы данных и Redis (если используется)
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