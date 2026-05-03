import asyncio
import aio_pika
from typing import cast
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel
from app.config.env import Env
from app.constants.rabbitmq import GExchanges, GQueues, GRoutingKeys
from app.utils.logger import logger
from typing import Dict, Any
from .policy import GRabbitMQPolicy


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

                await cls.upsert_policies()
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
            cls._connection is not None and not cls._connection.is_closed and cls._channel is not None and not cls._channel.is_closed
        )

    @classmethod
    async def close(cls):
        if cls._connection:
            await cls._connection.close()
            cls._connection = None
            cls._channel = None
            logger.info("RabbitMQ connection closed.")

    @classmethod
    async def upsert_policies(cls):
        try:
            if cls._channel is None:
                raise RuntimeError("RabbitMQClient not initialized.")

            logger.info("Setting up RabbitMQ policies...")
            ch = cls._channel

            await ch.declare_exchange(GExchanges.DOCUMENT_PROCESSING_EXCHANGE, aio_pika.ExchangeType.FANOUT, durable=True)
            await ch.declare_exchange(GExchanges.DOCUMENT_PROCESSING_EXCHANGE_DLX, aio_pika.ExchangeType.FANOUT, durable=True)

            doc_queue_a = await ch.declare_queue(GQueues.DOCUMENT_PROCESSING_QUEUE_A, durable=True)
            doc_queue_b = await ch.declare_queue(GQueues.DOCUMENT_PROCESSING_QUEUE_B, durable=True)
            dlx_queue = await ch.declare_queue(GQueues.DOCUMENT_PROCESSING_QUEUE_DLX, durable=True)

            await doc_queue_a.bind(GExchanges.DOCUMENT_PROCESSING_EXCHANGE, GRoutingKeys.DOCUMENT_PROCESSING_ROUTING_KEY)
            await doc_queue_b.bind(GExchanges.DOCUMENT_PROCESSING_EXCHANGE, GRoutingKeys.DOCUMENT_PROCESSING_ROUTING_KEY)
            await dlx_queue.bind(GExchanges.DOCUMENT_PROCESSING_EXCHANGE_DLX, GRoutingKeys.DOCUMENT_PROCESSING_ROUTING_KEY)

            pattern = "^" + GRoutingKeys.DOCUMENT_PROCESSING_ROUTING_KEY + "$"
            doc_q_definition: Dict[str, Any] = {
                "dead-letter-exchange": GExchanges.DOCUMENT_PROCESSING_EXCHANGE_DLX,
            }

            await GRabbitMQPolicy.upsert(GQueues.DOCUMENT_PROCESSING_QUEUE_A, pattern, doc_q_definition)

            await GRabbitMQPolicy.upsert(GQueues.DOCUMENT_PROCESSING_QUEUE_B, pattern, doc_q_definition)

            pattern = "^" + GRoutingKeys.DOCUMENT_PROCESSING_ROUTING_KEY + "$"
            dlx_q_definition: Dict[str, Any] = {
                "dead-letter-exchange": GExchanges.DOCUMENT_PROCESSING_EXCHANGE,
                "dead-letter-routing-key": GRoutingKeys.DOCUMENT_PROCESSING_ROUTING_KEY,
                "message-ttl": 5000,  # 5 seconds
            }

            await GRabbitMQPolicy.upsert(GQueues.DOCUMENT_PROCESSING_QUEUE_DLX, pattern, dlx_q_definition)

            logger.info("Policies upserted successfully.")
        except Exception as e:
            logger.error(f"Failed to upsert policies: {e}")
            raise e
