from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy import create_engine

from alembic import context
from db.base import Base
from models.transactions import Transaction
from core.config import load_config

env_config = load_config()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Alembic uses a sync engine — strip the _async suffix if present
_db_url = env_config.get("DATABASE_URL", "").replace("+psycopg_async", "+psycopg")
config.set_main_option("sqlalchemy.url", _db_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

TRANSACTIONS_TABLES = {"transactions"}

def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name not in TRANSACTIONS_TABLES:
        return False
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = env_config.get("DATABASE_URL", None)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version_transactions",
        include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(_db_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="alembic_version_transactions",
            include_object=include_object
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
