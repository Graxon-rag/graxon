from ..databases.minio.client import GMinioClient
from types_aiobotocore_s3 import S3Client
from app.utils.logger import logger
from app.config.env import Env
from typing import cast
from io import BytesIO
import json
import uuid
import os


class MinioUploadClient:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.minio_session = GMinioClient.get_session()
        self.minio_endpoint = f"http://{Env.MINIO_HOST}:{Env.MINIO_PORT}"
        self.bucket = self.org_id

    def _get_multipart_key(self, document_id: uuid.UUID, filename: str):
        return f"pro_{self.project_id}/doc_{document_id}/{filename}"

    async def multipart_upload_init(self, document_id: uuid.UUID, filename: str) -> dict:
        try:
            async with self.minio_session.client(  # type: ignore[attr-defined]
                "s3",
                endpoint_url=self.minio_endpoint,
                aws_access_key_id=Env.MINIO_ROOT_USER,
                aws_secret_access_key=Env.MINIO_ROOT_PASSWORD,
                region_name=Env.MINIO_REGION,
            ) as _s3_client:
                s3_client = cast(S3Client, _s3_client)

                key = self._get_multipart_key(document_id, filename)

                # Ensure bucket exists
                try:
                    await s3_client.head_bucket(Bucket=self.bucket)
                except Exception:
                    await s3_client.create_bucket(Bucket=self.bucket)

                res = await s3_client.create_multipart_upload(Bucket=self.bucket, Key=key)

                return {"document_id": document_id, "upload_id": res.get("UploadId"), "key": res.get("Key")}
        except Exception as e:
            logger.error({"message": "Failed to initiate multipart upload", "error": str(e)})
            raise e

    async def get_multipart_presigned_url(self, document_id: uuid.UUID, upload_id: str, key: str, part_number: int) -> dict:
        try:
            async with self.minio_session.client(  # type: ignore[attr-defined]
                "s3",
                endpoint_url=self.minio_endpoint,
                aws_access_key_id=Env.MINIO_ROOT_USER,
                aws_secret_access_key=Env.MINIO_ROOT_PASSWORD,
                region_name=Env.MINIO_REGION,
            ) as _s3_client:
                s3_client = cast(S3Client, _s3_client)

                presigned_url = await s3_client.generate_presigned_url(
                    ClientMethod="upload_part",
                    Params={
                        "Bucket": self.bucket,
                        "Key": key,
                        "UploadId": upload_id,
                        "PartNumber": part_number,
                    },
                    ExpiresIn=3600,
                )
                return {
                    "url": presigned_url,
                    "part_number": part_number,
                }
        except Exception as e:
            logger.error({"message": "Failed to get multipart presigned url", "error": str(e)})
            raise e

    async def complete_multipart_upload(self, document_id: uuid.UUID, upload_id: str, key: str):
        pass
