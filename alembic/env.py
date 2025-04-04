from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from src.db.database import Base
from src.core.config import settings

# Настройка логирования
config = context.config
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для миграций
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Запуск миграций в оффлайн-режиме."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

async def do_run_migrations():
    """Асинхронный запуск миграций."""
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
        echo=True
    )
    async with connectable.connect() as connection:
        await connection.run_sync(lambda sync_conn: context.configure(
            connection=sync_conn,
            target_metadata=target_metadata
        ))
        await connection.run_sync(lambda sync_conn: context.run_migrations())

def run_migrations_online() -> None:
    """Запуск миграций в онлайн-режиме."""
    import asyncio
    asyncio.run(do_run_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()