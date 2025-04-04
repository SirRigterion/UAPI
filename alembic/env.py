from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

from src.core.config import settings
from src.db.models import Base

# Alembic config
config = context.config
config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL.replace('%', '%%'))

# Enable logging
if config.config_file_name:
    fileConfig(config.config_file_name)

# Metadata from models
target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(
        url=settings.SYNC_DATABASE_URL.replace('%', '%%'),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()