from fastapi import FastAPI
from src.auth.routes import router as auth_router
from src.user.routes import router as user_router
from src.chat.routes import router as chat_router
from src.article.routes import router as article_router
from src.task.routes import router as task_router
from src.admin.routes import router as admin_router
from src.db.database import Base, engine, startup as db_startup
from src.db.models import Role, User, TaskStatus, TaskPriority
from sqlalchemy.future import select
from src.auth.routes import hash_password
from src.core.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(chat_router)
app.include_router(article_router)
app.include_router(task_router)
app.include_router(admin_router)

async def wait_for_db(max_attempts=10, delay=2):
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
    try:
        await wait_for_db()  # Ожидание базы данных
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with engine.connect() as conn:
            # Инициализация ролей
            result = await conn.execute(select(Role))
            roles = result.fetchall()
            if not roles:
                await conn.execute(
                    Role.__table__.insert().values([
                        {"role_id": 1, "role_name": "пользователь"},
                        {"role_id": 2, "role_name": "администратор"}
                    ])
                )
                logger.info("Роли по умолчанию успешно созданы")

            # Инициализация статусов задач
            result = await conn.execute(select(TaskStatus))
            statuses = result.fetchall()
            if not statuses:
                await conn.execute(
                    TaskStatus.__table__.insert().values([
                        {"status_id": 1, "status_name": "ACTIVE"},
                        {"status_id": 2, "status_name": "POSTPONED"},
                        {"status_id": 3, "status_name": "COMPLETED"}
                    ])
                )
                logger.info("Статусы задач по умолчанию успешно созданы")

            # Инициализация приоритетов задач
            result = await conn.execute(select(TaskPriority))
            priorities = result.fetchall()
            if not priorities:
                await conn.execute(
                    TaskPriority.__table__.insert().values([
                        {"priority_id": 1, "priority_name": "LOW"},
                        {"priority_id": 2, "priority_name": "MEDIUM"},
                        {"priority_id": 3, "priority_name": "HIGH"}
                    ])
                )
                logger.info("Приоритеты задач по умолчанию успешно созданы")

            # Инициализация администратора
            result = await conn.execute(select(User).where(User.email == "admin@example.com"))
            admin_user = result.scalar_one_or_none()
            if not admin_user:
                hashed_password = hash_password("string111")
                await conn.execute(
                    User.__table__.insert().values({
                        "username": "admin",
                        "full_name": "Админ Админов",
                        "email": "admin@example.com",
                        "hashed_password": hashed_password,
                        "role_id": 2
                    })
                )
                logger.info("Стандартный администратор успешно создан")
            else:
                logger.info("Стандартный администратор уже существует")

            await conn.commit()  # Коммит всех изменений

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