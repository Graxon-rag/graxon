import asyncio
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.config.env import Env
from app.utils.logger import logger

class GNeo4jClient:
    _instance: AsyncDriver | None = None

    @classmethod
    async def init(cls) -> AsyncDriver | None:
        """Initializes the Neo4j Async driver with a retry policy."""
        if cls._instance is not None:
            return cls._instance

        uri = f"bolt://{Env.NEO4J_HOST}:{Env.NEO4J_PORT}" 
        user = Env.NEO4J_USERNAME
        password = Env.NEO4J_PASSWORD
        
        if user is None or password is None:
            raise RuntimeError("NEO4J_USERNAME or NEO4J_PASSWORD is not set in environment variables")

        max_retries = 3
        retry_interval = 5

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Connecting to Neo4j (Attempt {attempt}/{max_retries})...")

                # Initialize the Async Driver
                driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
                
                # Verify connectivity (Liveness check)
                await driver.verify_connectivity()

                cls._instance = driver
                logger.info(f"Connected to Neo4j successfully.")
                return cls._instance

            except Exception as e:
                logger.error(f"Neo4j connection failed: {e}")
                if attempt < max_retries:
                    logger.info(f"Retrying Neo4j in {retry_interval}s...")
                    await asyncio.sleep(retry_interval)
                else:
                    logger.critical("Could not connect to Neo4j after multiple attempts.")
                    raise e

    @classmethod
    def get_driver(cls) -> AsyncDriver:
        """Returns the initialized Neo4j driver."""
        if cls._instance is None:
            raise RuntimeError("GNeo4jClient not initialized. Call init() first.")
        return cls._instance

    @classmethod
    async def is_healthy(cls) -> bool:
        """Health check for readiness probes."""
        if cls._instance is None:
            return False
        try:
            # verify_connectivity performs a low-level handshake
            await cls._instance.verify_connectivity()
            return True
        except Exception:
            return False

    @classmethod
    async def close(cls):
        """Gracefully close the Neo4j driver pool."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
            logger.info("Neo4j driver closed.")
