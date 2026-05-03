import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Env:
    """
    A class that contains constants for environment variables used in the service.
    """
    # Samvadam
    PORT: int = int(os.getenv("PORT", 8000))
    ENV_TYPE: str = os.getenv("ENV_TYPE", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    DOCS_USERNAME: str = os.getenv("DOCS_USERNAME", "admin")
    DOCS_PASSWORD: str = os.getenv("DOCS_PASSWORD", "admin")
    GRAXON_PUBLIC_URL: str = os.getenv("SAMVADAM_PUBLIC_URL", "http://localhost:8888")

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # Postgresql
    POSTGRESQL_USERNAME: str | None = os.getenv("POSTGRESQL_USERNAME", None)
    POSTGRESQL_PASSWORD: str | None = os.getenv("POSTGRESQL_PASSWORD", None)
    PGBOUNCER_HOST: str = os.getenv("PGBOUNCER_HOST", "localhost")
    PGBOUNCER_PORT: int = int(os.getenv("PGBOUNCER_PORT", 5433))

    # qDrant
    QDRANT_HOST: str | None = os.getenv("QDRANT_HOST", None)
    QDRANT_PORT: int | None = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_GRPC_PORT: int | None = int(os.getenv("QDRANT_GRPC_PORT", 6334))

    # Neo4j
    NEO4J_HOST: str | None = os.getenv("NEO4J_HOST", None)
    NEO4J_PORT: int | None = int(os.getenv("NEO4J_PORT", 7687))
    NEO4J_USERNAME: str | None = os.getenv("NEO4J_USERNAME", None)
    NEO4J_PASSWORD: str | None = os.getenv("NEO4J_PASSWORD", None)

    # Minio
    MINIO_HOST: str | None = os.getenv("MINIO_HOST", None)
    MINIO_PORT: int | None = int(os.getenv("MINIO_PORT", 9000))
    MINIO_ROOT_USER: str | None = os.getenv("MINIO_ROOT_USER", None)
    MINIO_ROOT_PASSWORD: str | None = os.getenv("MINIO_ROOT_PASSWORD", None)
    MINIO_REGION: str | None = os.getenv("MINIO_REGION", "ap-south-1")

    # Rabbitmq
    RABBITMQ_HOST: str | None = os.getenv("RABBITMQ_HOST", None)
    RABBITMQ_PORT: int | None = int(os.getenv("RABBITMQ_PORT", 5672))
    RABBITMQ_USER: str | None = os.getenv("RABBITMQ_USER", None)
    RABBITMQ_PASSWORD: str | None = os.getenv("RABBITMQ_PASSWORD", None)
    RABBITMQ_MANAGEMENT_PORT: int | None = int(os.getenv("RABBITMQ_MANAGEMENT_PORT", 15672))
    DOCUMENT_CONSUMER_COUNT: int = int(os.getenv("DOCUMENT_CONSUMER_COUNT", 5))
