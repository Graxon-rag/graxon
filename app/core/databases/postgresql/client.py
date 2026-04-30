from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from app.config.env import Env
from app.utils.logger import logger
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy import text
import asyncio


class GPostgresqlClient:
    # Single engine for "graxon"
    _engine: AsyncEngine | None = None

    @classmethod
    async def init(cls) -> AsyncEngine | None:
        if cls._engine is not None:
            return cls._engine
        
        max_retries = 3
        retry_interval = 5  # seconds

        for attempt in range(1, max_retries + 1):
            logger.info(f"Connecting to Postgresql (Attempt {attempt}/{max_retries})...")
            try:
                if cls._engine is None:
                    username = Env.POSTGRESQL_USERNAME
                    password = Env.POSTGRESQL_PASSWORD
                    host = Env.PGBOUNCER_HOST   # "localhost"
                    port = Env.PGBOUNCER_PORT   # 5433

                    full_url = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/graxon"

                    cls._engine = create_async_engine(
                        full_url,
                        echo=False,
                        pool_size=5,
                        max_overflow=2,
                        connect_args={
                            "prepared_statement_cache_size": 0,
                            "statement_cache_size": 0,
                        }
                    )
                    async with cls._engine.connect() as conn:
                        await conn.execute(text("SELECT 1"))
                    
                    logger.info("Connected to Postgresql.")
                    return cls._engine

            except Exception as e:
                logger.error(f"Failed to connect to Postgresql: {e}")
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_interval} seconds...")
                    await asyncio.sleep(retry_interval)
                else:
                    raise e

    @classmethod
    def get_engine(cls) -> AsyncEngine:
        if cls._engine is None:
            raise RuntimeError("PostgresqlClient not initialized.")
        return cls._engine


    @classmethod
    @asynccontextmanager
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        """
        Usage:
            async with get_session() as session:
                session.add(obj)
                await session.commit()
        """
        engine = cls.get_engine()
        session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Transaction rolled back: {e}")
                raise
            finally:
                await session.close()

    @classmethod
    async def postgresql_readiness_probe(cls) -> bool:
        """
        Checks DB health by running SELECT 1 through PgBouncer → Postgres.
        """
        try:
            engine = cls.get_engine()
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error({"message": "Readiness probe failed for graxon", "error": str(e)})
            raise
