import asyncio
import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError
from typing import Optional

from app.config.env import Env
from app.utils.logger import logger


class GRedisClient:
    _instance: Optional[Redis] = None

    @classmethod
    async def init(cls) -> Redis | None:
        """Initialize Redis client with retry logic."""
        if cls._instance is not None:
            return cls._instance

        redis_host = Env.REDIS_HOST
        redis_port = Env.REDIS_PORT
        redis_password = Env.REDIS_PASSWORD

        if not redis_password:
            raise RuntimeError("REDIS_PASSWORD is not set in environment variables")

        redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"

        max_retries = 3
        retry_interval = 5  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Connecting to Redis (Attempt {attempt}/{max_retries})...")

                client: Redis = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                    retry_on_timeout=True,
                )

                await client.ping() # type: ignore

                cls._instance = client
                logger.info("Connected to Redis")
                return cls._instance

            except (ConnectionError, TimeoutError) as e:
                logger.error(f"Redis connection failed: {e}")

                if attempt < max_retries:
                    logger.info(f"Retrying Redis in {retry_interval}s...")
                    await asyncio.sleep(retry_interval)
                else:
                    logger.critical("Could not connect to Redis after retries.")
                    raise

    @classmethod
    def get_client(cls) -> Redis:
        """Return initialized Redis instance."""
        if cls._instance is None:
            raise RuntimeError("RedisClient not initialized. Call init() first.")
        return cls._instance

    @classmethod
    async def is_healthy(cls) -> bool:
        """Health check for readiness/liveness probes."""
        if cls._instance is None:
            return False

        try:
            return await cls._instance.ping()  # type: ignore
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    @classmethod
    async def close(cls) -> None:
        """Gracefully close Redis connection."""
        if cls._instance:
            await cls._instance.aclose()
            cls._instance = None
            logger.info("Redis connection closed.")