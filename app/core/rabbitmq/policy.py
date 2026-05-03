from app.utils.logger import logger
from app.config.env import Env
from typing import Dict, Any
import httpx


class GRabbitMQPolicy:
    @staticmethod
    async def upsert(name: str, pattern: str, definition: Dict[str, Any]):
        try:
            host = Env.RABBITMQ_HOST
            m_port = Env.RABBITMQ_MANAGEMENT_PORT
            user = Env.RABBITMQ_USER
            password = Env.RABBITMQ_PASSWORD

            if user is None or password is None:
                raise RuntimeError("RABBITMQ_USER or RABBITMQ_PASSWORD is not set in environment variables")

            if host is None or m_port is None:
                raise RuntimeError("RABBITMQ_HOST or RABBITMQ_MANAGEMENT_PORT is not set in environment variables")

            is_dev = Env.ENV_TYPE == "development"
            scheme = "http" if is_dev else "https"
            vhost = "%2f"

            payload: Dict[str, Any] = {
                "pattern": pattern,
                "definition": definition,
                "apply-to": "queues",
                "priority": 0,
            }

            url = f"{scheme}://{host}:{m_port}/api/policies/{vhost}/{name}"

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    url,
                    json=payload,
                    auth=(user, password),
                )

            if response.status_code not in (200, 201, 204):
                logger.error(f"RabbitMQ Upsert Policy API error: {response.status_code} {response.text}")
                raise RuntimeError(f"API error: status {response.status_code}")

            logger.info(f" [✓] Policy '{name}' synchronized successfully")

        except Exception as e:
            logger.error(f"Failed to upsert RabbitMQ policy: {e}")
            raise e
