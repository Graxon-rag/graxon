from .client import GRabbitMQClient
from app.utils.logger import logger
from app.constants.rabbitmq import GQueues
from ..services.document_service import DocumentService
from ..schemas.document_schema import DocumentGetSchema, DocumentStatusMQSchema
from ..schemas import processor_schema as ps
from app.constants.document import DocumentStatus
from aio_pika.abc import AbstractIncomingMessage
from .producer import GMQDocumentProducer
from ..workflow.document_workflow import DocumentWorkflow
import uuid


class GMQDocumentConsumer:

    async def consume_document_processing_queue(self):
        try:
            logger.info(f"[✓] Started consuming from queue: {GQueues.DOCUMENT_PROCESSING_QUEUE}")

            channel = await GRabbitMQClient.create_channel()

            await channel.set_qos(prefetch_count=1)  # Set the prefetch count to 1 so we only get one message at a time from the queue and process it

            queue = await channel.get_queue(GQueues.DOCUMENT_PROCESSING_QUEUE)

            await queue.consume(self._on_document_processing_message, no_ack=False)

            logger.info(f"[✓] Consuming from queue: {GQueues.DOCUMENT_PROCESSING_QUEUE}")
        except Exception as e:
            logger.error({"message": "Failed to consume message", "error": str(e)})
            raise e

    async def consume_document_status_queue(self):
        try:
            logger.info(f"[✓] Started consuming from queue: {GQueues.DOCUMENT_STATUS_QUEUE}")

            channel = await GRabbitMQClient.create_channel()

            await channel.set_qos(prefetch_count=1)  # Set the prefetch count to 1 so we only get one message at a time from the queue and process it

            queue = await channel.get_queue(GQueues.DOCUMENT_STATUS_QUEUE)

            await queue.consume(self._on_document_status_message, no_ack=False)

            logger.info(f"[✓] Consuming from queue: {GQueues.DOCUMENT_STATUS_QUEUE}")
        except Exception as e:
            logger.error({"message": "Failed to consume message", "error": str(e)})
            raise e

    async def _on_document_processing_message(self, message: AbstractIncomingMessage):
        async with message.process(requeue=False, ignore_processed=True):
            body = message.body.decode()
            retry_count = self._get_retry_count(message)
            data = ps.ProcessParams.model_validate_json(body)
            try:
                logger.info({"message": "Received message", "retry_count": retry_count, "document": data.model_dump(mode="json", exclude_none=True)})

                if retry_count > 3:
                    logger.error({"message": "Max retries exceeded, skipping message", "retry_count": retry_count, "document": data.model_dump(mode="json", exclude_none=True)})

                    await GMQDocumentProducer.publish_to_status_exchange(DocumentStatusMQSchema(org_id=data.org_id, project_id=data.project_id, id=data.doc_id, status=DocumentStatus.FAILED))

                    await message.ack()  # ack to drop it permanently, not reject/nack
                    return

                await self._process_document(data)

                await message.ack()  # We are done with the message
            except Exception as e:
                logger.error(f"Failed to process message, sending nack → DLX: {e}")
                await message.nack(requeue=False)  # sends to DLX
                raise e

    async def _on_document_status_message(self, message: AbstractIncomingMessage):
        async with message.process(requeue=False, ignore_processed=True):
            try:
                body = message.body.decode()
                doc_status = DocumentStatusMQSchema.model_validate_json(body)
                service = DocumentService(org_id=doc_status.org_id, project_id=doc_status.project_id)
                await service.change_document_status(doc_status.id, doc_status.status)

                await message.ack()  # We are done with the message
            except Exception as e:
                logger.error({"message": "Failed to update document status in MQ Consumer, skipping this again", "error": str(e)})
                await message.ack()  # We are done with the message
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

    async def _process_document(self, data: ps.ProcessParams):
        file_type = data.file_type
        match file_type:
            case ps.FileType.AUDIO:
                pass
            case ps.FileType.IMAGE:
                pass
            case ps.FileType.VIDEO:
                pass
            case ps.FileType.CODE:
                pass
            case ps.FileType.TEXT:
                pass
            case ps.FileType.JSON:
                pass
            case ps.FileType.PDF:
                pass
            case ps.FileType.MARKDOWN:
                pass
            case ps.FileType.DOC:
                pass
            case ps.FileType.PPT:
                pass
            case ps.FileType.EXCEL:
                pass
            case ps.FileType.HTML:
                pass
            case ps.FileType.CSV:
                pass
            case ps.FileType.XML:
                pass
            case ps.FileType.YAML:
                pass
            case _:
                raise ValueError(f"Unsupported file type: {file_type.value.lower()}")
