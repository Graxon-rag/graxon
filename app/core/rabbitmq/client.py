import asyncio
import aio_pika
from typing import cast
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel
from app.config.env import Env
from app.utils.logger import logger

class GRabbitMQClient:
    _connection: AbstractRobustConnection | None = None
    _channel: AbstractRobustChannel | None = None

    @classmethod
    async def init(cls) -> AbstractRobustConnection | None:
        if cls._connection is not None and not cls._connection.is_closed:
            return cls._connection

        host = Env.RABBITMQ_HOST
        port = Env.RABBITMQ_PORT
        user = Env.RABBITMQ_USER
        password = Env.RABBITMQ_PASSWORD
        
        if user is None or password is None:
            raise RuntimeError("RABBITMQ_USER or RABBITMQ_PASSWORD is not set in environment variables")

        if host is None or port is None:
            raise RuntimeError("RABBITMQ_HOST or RABBITMQ_PORT is not set in environment variables")
        
        rabbitmq_url = (
            f"amqp://{Env.RABBITMQ_USER}:{Env.RABBITMQ_PASSWORD}@"
            f"{Env.RABBITMQ_HOST}:{Env.RABBITMQ_PORT}/"
        )

        for attempt in range(1, 4):
            try:
                logger.info(f"Connecting to RabbitMQ (Attempt {attempt}/3)...")
                
                connection = await aio_pika.connect_robust(rabbitmq_url)
                cls._connection = connection
                
                # Use 'cast' to tell the type checker this is a robust channel
                channel = await connection.channel()
                cls._channel = cast(AbstractRobustChannel, channel)
                
                logger.info("Connected to RabbitMQ successfully.")
                return cls._connection

            except Exception as e:
                logger.error(f"RabbitMQ connection failed: {e}")
                if attempt < 3:
                    await asyncio.sleep(5)
                else:
                    raise e

    @classmethod
    def get_channel(cls) -> AbstractRobustChannel:
        if cls._channel is None:
            raise RuntimeError("RabbitMQClient not initialized.")
        return cls._channel

    @classmethod
    async def is_healthy(cls) -> bool:
        # Check both connection and channel status
        return (
            cls._connection is not None 
            and not cls._connection.is_closed 
            and cls._channel is not None 
            and not cls._channel.is_closed
        )

    @classmethod
    async def close(cls):
        if cls._connection:
            await cls._connection.close()
            cls._connection = None
            cls._channel = None
            logger.info("RabbitMQ connection closed.")
