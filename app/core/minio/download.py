from ..databases.minio.client import GMinioClient
from types_aiobotocore_s3 import S3Client
from app.utils.logger import logger
from typing import cast, Optional
from app.config.env import Env
import uuid
import os


class MinioDownloadClient:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.minio_session = GMinioClient.get_session()
        self.minio_endpoint = f"http://{Env.MINIO_HOST}:{Env.MINIO_PORT}"
        self.bucket = self.org_id

    async def download_file(self, bucket: str, key: str, download_path: str, file_name: Optional[str] = None):
        try:
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
            logger.error({"message": "Failed to download file", "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            raise e
