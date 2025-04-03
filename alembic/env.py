from logging.config import fileConfig
from alembic import context
from src.db.models import Base
from src.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Устанавливаем URL базы данных из settings без интерполяции configparser
config.attributes['sqlalchemy.url'] = settings.DATABASE_URL

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.attributes.get('sqlalchemy.url', config.get_main_option("sqlalchemy.url"))
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async engine."""
    from src.db.database import engine  # Импортируем асинхронный движок из проекта
    
    connectable = engine

    async def do_run_migrations():
        async with connectable.connect() as connection:
            # Выполняем миграции синхронно внутри run_sync
            await connection.run_sync(do_configure_and_run)

    def do_configure_and_run(sync_conn):
        context.configure(
            connection=sync_conn,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

    import asyncio
    asyncio.run(do_run_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()