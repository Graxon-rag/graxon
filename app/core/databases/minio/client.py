import asyncio
import aioboto3
from types_aiobotocore_s3 import S3Client
from typing import cast
from app.config.env import Env
from app.utils.logger import logger


class GMinioClient:
    _session: aioboto3.Session | None = None

    @classmethod
    async def init(cls) -> aioboto3.Session | None:
        if cls._session is not None:
            return cls._session

        host = Env.MINIO_HOST
        port = Env.MINIO_PORT
        if host is None or port is None:
            raise RuntimeError("MINIO_HOST or MINIO_PORT is not set in environment variables")
        access_key = Env.MINIO_ROOT_USER
        secret_key = Env.MINIO_ROOT_PASSWORD

        if access_key is None or secret_key is None:
            raise RuntimeError("MINIO_ROOT_USER or MINIO_ROOT_PASSWORD is not set in environment variables")

        endpoint = f"http://{host}:{port}"
        max_retries = 3
        retry_interval = 5

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Connecting to MinIO (Attempt {attempt}/{max_retries})...")

                session = aioboto3.Session()

                async with session.client(  # type: ignore[attr-defined]
                    's3',
                    endpoint_url=endpoint,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name="us-east-1"
                ) as _s3:
                    s3 = cast(S3Client, _s3)
                    await s3.list_buckets()

                cls._session = session
                logger.info("Connected to MinIO successfully.")
                return cls._session

            except Exception as e:
                logger.error(f"MinIO connection failed: {e}")
                if attempt < max_retries:
                    logger.info(f"Retrying MinIO in {retry_interval}s...")
                    await asyncio.sleep(retry_interval)
                else:
                    logger.critical("Could not connect to MinIO after 3 attempts.")
                    raise

    @classmethod
    def get_session(cls) -> aioboto3.Session:
        if cls._session is None:
            raise RuntimeError("GMinioClient not initialized. Call init() first.")
        return cls._session

    @classmethod
    async def is_healthy(cls) -> bool:
        if cls._session is None:
            return False
        try:
            endpoint = f"http://{Env.MINIO_HOST}:{Env.MINIO_PORT}"
            async with cls._session.client(  # type: ignore[attr-defined]
                's3',
                endpoint_url=endpoint,
                aws_access_key_id=Env.MINIO_ROOT_USER,
                aws_secret_access_key=Env.MINIO_ROOT_PASSWORD,
                region_name=Env.MINIO_REGION
            ) as _s3:
                s3 = cast(S3Client, _s3)
                await s3.list_buckets()
            return True
        except Exception:
            return False
