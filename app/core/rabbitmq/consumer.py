from .client import GRabbitMQClient
from app.utils.logger import logger
from app.constants.rabbitmq import GQueues, GRoutingKeys, GExchanges
from ..schemas.document_schema import DocumentGetSchema
from aio_pika.abc import AbstractIncomingMessage


class GMQDocumentConsumer:

    async def consume(self):
        try:
            logger.info(f"[✓] Started consuming from queue: {GQueues.DOCUMENT_PROCESSING_QUEUE}")

            channel = await GRabbitMQClient.create_channel()

            await channel.set_qos(prefetch_count=1)  # Set the prefetch count to 1 so we only get one message at a time from the queue and process it

            queue = await channel.get_queue(GQueues.DOCUMENT_PROCESSING_QUEUE)

            await queue.consume(self._on_message, no_ack=False)

            logger.info(f"[✓] Consuming from queue: {GQueues.DOCUMENT_PROCESSING_QUEUE}")
        except Exception as e:
            logger.error({"message": "Failed to consume message", "error": str(e)})
            raise e

    async def _on_message(self, message: AbstractIncomingMessage):
        async with message.process(requeue=False, ignore_processed=True):
            try:

                body = message.body.decode()
                retry_count = self._get_retry_count(message)

                document = DocumentGetSchema.model_validate_json(body)
                logger.info({"message": "Received message", "retry_count": retry_count, "document": document.model_dump(mode="json")})

                if retry_count > 3:
                    logger.error({"message": "Max retries exceeded, skipping message", "retry_count": retry_count, "document": document.model_dump(mode="json")})
                    await message.ack()  # ack to drop it permanently, not reject/nack
                    return

                await self._process(document)

                await message.ack()  # We are done with the message
            except Exception as e:
                logger.error(f"Failed to process message, sending nack → DLX: {e}")
                await message.nack(requeue=False)  # sends to DLX
                raise e

    def _get_retry_count(self, message: AbstractIncomingMessage) -> int:
        try:
            x_death = message.headers.get("x-death")
            if x_death and isinstance(x_death, list) and len(x_death) > 0:
                first = x_death[0]
                if isinstance(first, dict):
                    count = first.get("count", 0)
                    if isinstance(count, (int, float)):
                        return int(count)
            return 0
        except Exception:
            return 0

    async def _process(self, document: DocumentGetSchema):
        raise NotImplementedError
