from logging.config import fileConfig
from typing import List
from app.config.env import Env
from app.core.databases.postgresql.models import Base
from sqlalchemy import engine_from_config
from app.constants.postgresql import PGTables, PGDatabase
from sqlalchemy import pool
from sqlalchemy import create_engine

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

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

# Define the tables this graxon service is responsible for
# ** Please do not add the tables which are not owned by this graxon service **
GRAXON_OWNED_TABLES = [PGTables.RERANKER_MODEL_TABLE]


def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table":
        # 1. If the table is in our 'Owned' list, track changes
        if name in GRAXON_OWNED_TABLES:
            return True
        # 2. Always ignore 'alembic_version' tables to avoid loops
        if name.startswith("alembic_version"):
            return False
        # 3. If it's any other table (like 'localities'), ignore it
        return False

    # For indexes and constraints, only include them if they belong to our tables
    return True


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    db_names: List[str] = [PGDatabase.GRAXON_DATABASE]  # TODO: make this dynamic
    host = Env.PGBOUNCER_HOST
    port = Env.PGBOUNCER_PORT
    username = Env.POSTGRESQL_USERNAME
    password = Env.POSTGRESQL_PASSWORD
    base_url = f"postgresql://{username}:{password}@{host}:{port}".rstrip('/')

    for db_name in db_names:
        url = f"{base_url}/{db_name}"
        print(f"Migrating: {db_name}")
        connectable = create_engine(url)

        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object, version_table='alembic_version_graxon')
            with context.begin_transaction():
                context.run_migrations()


run_migrations_online()