from ..databases.minio.client import GMinioClient
from app.config.env import Env
from types_aiobotocore_s3 import S3Client
from fastapi import UploadFile
from ..schemas.document_schema import DocumentGetSignedUrlSchema
from app.utils.logger import logger
from typing import cast, Tuple
import uuid


class MinioHelper:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.minio_session = GMinioClient.get_session()
        self.minio_endpoint = f"http://{Env.MINIO_HOST}:{Env.MINIO_PORT}"
        self.bucket = self.org_id

    async def upload_file(self, file: UploadFile, file_type: str, file_name: str, document_name_id: str) -> Tuple[str, str]:
        try:

            document_key = f"{self.project_id}/{document_name_id}/{file.filename}"

            async with self.minio_session.client(  # type: ignore[attr-defined]
                "s3",
                endpoint_url=self.minio_endpoint,
                aws_access_key_id=Env.MINIO_ROOT_USER,
                aws_secret_access_key=Env.MINIO_ROOT_PASSWORD,
                region_name=Env.MINIO_REGION,
            ) as _s3_client:

                s3_client = cast(S3Client, _s3_client)

                # Ensure bucket exists
                try:
                    await s3_client.head_bucket(Bucket=self.bucket)
                except Exception:
                    await s3_client.create_bucket(Bucket=self.bucket)

                file.file.seek(0)

                await s3_client.put_object(
                    Bucket=self.bucket,
                    Key=document_key,
                    Body=file.file,
                    ContentType=file_type,
                    Metadata={
                        "org_id": self.org_id,
                        "project_id": str(self.project_id),
                        "filename": file_name
                    }   
                )

                signed_url = await self.get_signed_url(DocumentGetSignedUrlSchema(org_id=self.org_id, project_id=self.project_id, bucket=self.bucket, key=document_key), 900)
                return (document_key, signed_url)
        except Exception as e:
            logger.error({"message": "Failed to upload file", "error": str(e)})
            raise e

    async def get_signed_url(self, document: DocumentGetSignedUrlSchema, ttl: int = 900) -> str:  # 15 minutes ttl
        try:
            key = document.key

            async with self.minio_session.client(  # type: ignore[attr-defined]
                "s3",
                endpoint_url=self.minio_endpoint,
                aws_access_key_id=Env.MINIO_ROOT_USER,
                aws_secret_access_key=Env.MINIO_ROOT_PASSWORD,
                region_name=Env.MINIO_REGION,
            ) as _s3_client:

                s3_client = cast(S3Client, _s3_client)

                # Ensure bucket exists
                try:
                    await s3_client.head_bucket(Bucket=self.bucket)
                except Exception:
                    raise Exception(f"Bucket {self.bucket} does not exist")

                signed_url = await s3_client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={
                        "Bucket": self.bucket,
                        "Key": key,
                    },
                    ExpiresIn=ttl,  # 15 minutes
                )

                return signed_url
        except Exception as e:
            logger.error({"message": "Failed to get signed url", "error": str(e)})
            raise e
