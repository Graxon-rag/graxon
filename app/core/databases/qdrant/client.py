import asyncio
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from app.config.env import Env
from app.utils.logger import logger

class GQdrantClient:
    _instance: AsyncQdrantClient | None = None

    @classmethod
    async def init(cls) -> AsyncQdrantClient | None:
        """Initializes the Qdrant client with a retry policy."""
        if cls._instance is not None:
            return cls._instance

        host = Env.QDRANT_HOST
        port = Env.QDRANT_PORT
        grpc_port = Env.QDRANT_GRPC_PORT or 6334 # gRPC is faster for high-volume ops

        max_retries = 3
        retry_interval = 5

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Connecting to Qdrant (Attempt {attempt}/{max_retries})...")

                # AsyncQdrantClient for asynchronous operations
                client = AsyncQdrantClient(
                    host=host,
                    port=port,
                    grpc_port=grpc_port,
                    prefer_grpc=True, # Set to True for better performance
                    timeout=10
                )

                # Use get_collections as a reachability probe
                # This ensures the REST/gRPC interface is actually responding
                await client.get_collections()

                cls._instance = client
                logger.info("Connected to Qdrant successfully.")
                return cls._instance

            except Exception as e:
                logger.error(f"Qdrant connection failed: {e}")
                if attempt < max_retries:
                    logger.info(f"Retrying Qdrant in {retry_interval}s...")
                    await asyncio.sleep(retry_interval)
                else:
                    logger.critical("Could not connect to Qdrant after multiple attempts.")
                    raise e

    @classmethod
    def get_client(cls) -> AsyncQdrantClient:
        """Returns the initialized Qdrant instance."""
        if cls._instance is None:
            raise RuntimeError("GQdrantClient not initialized. Call init() first.")
        return cls._instance

    @classmethod
    async def is_healthy(cls) -> bool:
        """Health check for readiness probes."""
        if cls._instance is None:
            return False
        try:
            # Qdrant's internal health check
            result =  await cls._instance.get_collections()
            if result:
                return True
            return False
        except Exception:
            return False

    @classmethod
    async def close(cls):
        """Gracefully close the Qdrant client."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
            logger.info("Qdrant client connection closed.")
