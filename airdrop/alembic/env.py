import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# ×™×™×‘×•× ×”-Base ×•×”×ž×•×“×œ×™× ×©×œ×š
from backend.app.db.database import Base
from backend.app.models.models import User # ×•×•×“× ×©×›×œ ×”×ž×•×“×œ×™× ×ž×™×•×‘××™× ×›××Ÿ

config = context.config

# ×”×’×“×¨×ª ×›×ª×•×‘×ª ×”-DB ×ž×ž×©×ª× ×™ ×¡×‘×™×‘×” (×›×ž×• ×‘-Railway)
db_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "pyformat"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
