from ..schemas.webhook_schema import WebhookSendParams, WebhookGetSchema
from app.constants.webhook import GRAXON_X_TOKEN
from app.utils.logger import logger
import asyncio
import httpx
import json


class WebhookConsumerHelper:
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def _send_single_webhook(
        self, client: httpx.AsyncClient, webhook: WebhookGetSchema, payload: dict
    ):
        try:
            headers = {
                "Content-Type": "application/json",
                GRAXON_X_TOKEN: webhook.token,
            }
            response = await client.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            logger.info(
                {
                    "message": "Webhook sent successfully",
                    "webhook_id": str(webhook.id),
                    "status_code": response.status_code,
                }
            )
        except Exception as e:
            # Catch and log errors per webhook so other endpoints are unaffected
            logger.error(
                {
                    "message": "Failed to send webhook to destination",
                    "webhook_id": str(webhook.id),
                    "url": webhook.url,
                    "error": str(e),
                }
            )
            raise e

    async def handle_webhook_send(self, data: WebhookSendParams):
        if not data.webhooks:
            return

        # Extracts and serializes only WebhookEventParams (id, event, data, created_at)
        if hasattr(data.event_data, "model_dump"):
            payload = data.event_data.model_dump(mode="json")  # Pydantic v2
        else:
            payload = json.loads(data.event_data.model_dump_json())       # Pydantic v1 fallback

        async with httpx.AsyncClient() as client:
            tasks = [
                self._send_single_webhook(client, webhook, payload)
                for webhook in data.webhooks
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
