from types_aiobotocore_s3.type_defs import CompletedPartTypeDef
from ..databases.minio.client import GMinioClient
from botocore.exceptions import ClientError
from types_aiobotocore_s3 import S3Client
from app.utils.logger import logger
from app.config.env import Env
from enum import Enum
from typing import cast
import uuid
import json


class AgentEnum(str, Enum):
    LLM = "llm"
    EMBEDDING = "embedding"
    SPARSE = "sparse"
    LEXICAL = "lexical"


class CheckpointMinioClient:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.minio_session = GMinioClient.get_session()
        self.minio_endpoint = f"http://{Env.MINIO_HOST}:{Env.MINIO_PORT}"
        self.bucket = self.org_id

    def _get_key(self, document_id: uuid.UUID, agent: AgentEnum, filename: str) -> str:
        return f"pro_{self.project_id}/doc_{document_id}/checkpoints/{agent.value}/{filename}"

    async def upload(self, document_id: uuid.UUID, agent: AgentEnum, start_chunk: int, end_chunk: int, data: dict) -> bool:
        try:
            filename = f"chunks_{start_chunk:d}_{end_chunk:d}.json"
            key = self._get_key(document_id, agent, filename)

            # Serialize the dictionary to bytes
            json_bytes = json.dumps(data).encode("utf-8")

            async with self.minio_session.client(  # type: ignore[attr-defined]
                "s3",
                endpoint_url=self.minio_endpoint,
                aws_access_key_id=Env.MINIO_ROOT_USER,
                aws_secret_access_key=Env.MINIO_ROOT_PASSWORD,
                region_name=Env.MINIO_REGION,
            ) as _s3_client:
                s3_client = cast(S3Client, _s3_client)

                await s3_client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=json_bytes,
                    ContentType="application/json"
                )

                logger.info({"message": "Uploaded checkpoint to MinIO", "key": key})
                return True

        except Exception as e:
            logger.error({"message": "Failed to upload checkpoint", "error": str(e)})
            raise e

    async def get(self, document_id: uuid.UUID, agent: AgentEnum, start_chunk: int, end_chunk: int) -> dict | None:
        try:
            filename = f"chunks_{start_chunk:d}_{end_chunk:d}.json"
            key = self._get_key(document_id, agent, filename)

            async with self.minio_session.client(  # type: ignore[attr-defined]
                "s3",
                endpoint_url=self.minio_endpoint,
                aws_access_key_id=Env.MINIO_ROOT_USER,
                aws_secret_access_key=Env.MINIO_ROOT_PASSWORD,
                region_name=Env.MINIO_REGION,
            ) as _s3_client:
                s3_client = cast(S3Client, _s3_client)

                response = await s3_client.get_object(
                    Bucket=self.bucket,
                    Key=key
                )

                async with response["Body"] as stream:
                    body_data = await stream.read()

                return json.loads(body_data.decode("utf-8"))

        except ClientError as e:
            # If the file does not exist, return None so the agent knows to run the API
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "NoSuchKey":
                return None

            logger.error({"message": "S3 ClientError while getting checkpoint", "error": str(e)})
            raise e
        except Exception as e:
            logger.error({"message": "Failed to get checkpoint", "error": str(e)})
            raise e

    async def delete_all_checkpoints(self, document_id: uuid.UUID) -> bool:
        """Used by the cleanup_agent to wipe the temporary folder after the pipeline finishes."""
        try:
            prefix = f"pro_{self.project_id}/doc_{document_id}/checkpoints/"

            async with self.minio_session.client(  # type: ignore[attr-defined]
                "s3",
                endpoint_url=self.minio_endpoint,
                aws_access_key_id=Env.MINIO_ROOT_USER,
                aws_secret_access_key=Env.MINIO_ROOT_PASSWORD,
                region_name=Env.MINIO_REGION,
            ) as _s3_client:
                s3_client = cast(S3Client, _s3_client)

                # Fetch all keys under the prefix
                paginator = s3_client.get_paginator("list_objects_v2")
                async for result in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                    if "Contents" in result:
                        objects_to_delete = [{"Key": obj["Key"]} for obj in result["Contents"]]  # type: ignore

                        await s3_client.delete_objects(
                            Bucket=self.bucket,
                            Delete={"Objects": objects_to_delete}  # type: ignore
                        )

                logger.info({"message": "Cleaned up all checkpoints", "document_id": str(document_id)})
                return True

        except Exception as e:
            logger.error({"message": "Failed to clean up checkpoints", "error": str(e)})
            raise e
