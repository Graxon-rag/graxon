from ..databases.minio.client import GMinioClient
from app.config.env import Env
from types_aiobotocore_s3 import S3Client
from fastapi import UploadFile
from ..schemas.document_schema import DocumentGetSignedUrlSchema
from app.utils.logger import logger
from typing import cast, Tuple, Optional, Any
from io import BytesIO
import json
import uuid
import os


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

    async def delete_file(self, bucket: str, key: str) -> bool:
        try:
            async with self.minio_session.client(  # type: ignore[attr-defined]
                "s3",
                endpoint_url=self.minio_endpoint,
                aws_access_key_id=Env.MINIO_ROOT_USER,
                aws_secret_access_key=Env.MINIO_ROOT_PASSWORD,
                region_name=Env.MINIO_REGION,
            ) as _s3_client:

                s3_client = cast(S3Client, _s3_client)

                # Check bucket exists
                try:
                    await s3_client.head_bucket(Bucket=self.bucket)
                except Exception:
                    raise Exception(f"Bucket {self.bucket} does not exist")

                # Delete object
                await s3_client.delete_object(
                    Bucket=self.bucket,
                    Key=key
                )

                return True

        except Exception as e:
            logger.error({"message": "Failed to delete file", "error": str(e)})
            raise e

    async def download_file(self, bucket: str, key: str, download_path: str, file_name: Optional[str] = None) -> str:
        try:
            async with self.minio_session.client(  # type: ignore[attr-defined]
                "s3",
                endpoint_url=self.minio_endpoint,
                aws_access_key_id=Env.MINIO_ROOT_USER,
                aws_secret_access_key=Env.MINIO_ROOT_PASSWORD,
                region_name=Env.MINIO_REGION,
            ) as s3_client:
                s3_client = cast(S3Client, s3_client)

                # Ensure bucket exists
                try:
                    await s3_client.head_bucket(Bucket=bucket)
                except Exception:
                    raise Exception(f"Bucket {bucket} does not exist")

                # Resolve file path
                file_name = file_name or os.path.basename(key)
                full_path = os.path.join(download_path, file_name)
                os.makedirs(download_path, exist_ok=True)

                # Get object
                response = await s3_client.get_object(Bucket=bucket, Key=key)

                # Try iter_chunks first, fallback to full read
                try:
                    with open(full_path, "wb") as f:
                        async for chunk in response["Body"].iter_chunks(1024 * 1024):
                            f.write(chunk)
                except AttributeError:
                    # iter_chunks not available — read full body
                    body = await response["Body"].read()
                    with open(full_path, "wb") as f:
                        f.write(body)

                return full_path

        except Exception as e:
            logger.error({"message": "Failed to download file", "error": str(e)})
        raise

    async def upload_json(self, json_file_name: str, json_data: dict[str, Any], document_name_id: str,) -> Tuple[str, str]:
        try:
            # Create object key
            document_key = (
                f"{self.project_id}/{document_name_id}/{json_file_name}.json"
            )

            # Convert JSON → bytes
            json_bytes = json.dumps(
                json_data,
                ensure_ascii=False,
                indent=2
            ).encode("utf-8")

            json_stream = BytesIO(json_bytes)

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

                # Upload JSON
                await s3_client.put_object(
                    Bucket=self.bucket,
                    Key=document_key,
                    Body=json_stream,
                    ContentType="application/json",
                    Metadata={
                        "org_id": self.org_id,
                        "project_id": str(self.project_id),
                        "file_type": "json",
                    },
                )

                signed_url = await self.get_signed_url(
                    DocumentGetSignedUrlSchema(
                        org_id=self.org_id,
                        project_id=self.project_id,
                        bucket=self.bucket,
                        key=document_key,
                    ),
                    900,
                )

                return (document_key, signed_url)

        except Exception as e:
            logger.error({
                "message": "Failed to upload JSON file",
                "error": str(e)
            })
            raise e

    async def download_json(self, json_file_name: str, document_name_id: str) -> dict[str, Any]:
        try:
            # Recreate the exact same deterministic key used during upload
            document_key = (
                f"{self.project_id}/{document_name_id}/{json_file_name}.json"
            )

            logger.info({
                "message": "Downloading JSON from Minio",
                "bucket": self.bucket,
                "key": document_key
            })

            async with self.minio_session.client(  # type: ignore[attr-defined]
                "s3",
                endpoint_url=self.minio_endpoint,
                aws_access_key_id=Env.MINIO_ROOT_USER,
                aws_secret_access_key=Env.MINIO_ROOT_PASSWORD,
                region_name=Env.MINIO_REGION,
            ) as _s3_client:

                s3_client = cast(S3Client, _s3_client)

                # Fetch the object from Minio
                response = await s3_client.get_object(
                    Bucket=self.bucket,
                    Key=document_key
                )

                # StreamingBody must be read asynchronously 
                async with response["Body"] as stream:
                    json_bytes = await stream.read()

                # Parse the UTF-8 bytes back to a dictionary
                json_data = json.loads(json_bytes.decode("utf-8"))
                return json_data

        except Exception as e:
            logger.error({
                "message": "Failed to download JSON file from Minio",
                "key": f"{self.project_id}/{document_name_id}/{json_file_name}.json",
                "error": str(e)
            })
            raise e
