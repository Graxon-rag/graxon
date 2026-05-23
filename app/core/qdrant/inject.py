from ..databases.qdrant.client import GQdrantClient
from qdrant_client import models
from typing import Tuple
from app.constants.qdrant import QDrant_MODEL_MAP
from app.utils.logger import logger
from qdrant_client.conversions.common_types import PointStruct
from ..schemas.chunk_schema import ChunkEmbedding, ChunkSparseEmbedding, Chunk
import uuid
import asyncio


class QdrantInjector:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.qdrant_client = GQdrantClient.get_client()
        logger.info("Qdrant Injector initialized.")

    async def inject(self, model_key: str, document_id: uuid.UUID, chunks: list[Chunk], chunk_embeddings: list[ChunkEmbedding], chunk_sparse_embeddings: list[ChunkSparseEmbedding]):
        try:
            dense_map = {e.chunk_id: e.embedding for e in chunk_embeddings}
            sparse_map = {e.chunk_id: e.embedding for e in chunk_sparse_embeddings}
            chunk_map = {c.chunk_id: c for c in chunks}

            coll, dense_vector_name = GQdrantClient._get_collection_vector_name(model_key)
            client = GQdrantClient.get_client()

            points: list[PointStruct] = []
            for chunk_id, chunk in chunk_map.items():
                dense_embedding = dense_map.get(chunk_id)
                sparse_embedding = sparse_map.get(chunk_id)

                if dense_embedding is None or sparse_embedding is None:
                    logger.warning(f"Missing embedding for chunk_id={chunk_id}, skipping.")
                    continue

                # GENERATE A DETERMINISTIC UUID BASED ON CHUNK_ID
                # NAMESPACE_DNS is a safe standard default to seed the hash
                deterministic_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

                points.append(PointStruct(
                    id=deterministic_id,
                    vector={
                        dense_vector_name: dense_embedding,
                        "sparse": models.SparseVector(
                            indices=sparse_embedding.indices.tolist(),
                            values=sparse_embedding.values.tolist(),
                        ),
                    },
                    payload={
                        "text": chunk.text,
                        "org_id": self.org_id,
                        "project_id": str(self.project_id),   # UUID → str
                        "document_id": str(document_id),      # UUID → str
                        "chunk_id": chunk_id,
                        "chunk_number": chunk.chunk_number,
                        "page_number": chunk.page_number,
                    },
                ))

            # Retry logic
            MAX_RETRIES = 3

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    client.upload_points(
                        collection_name=coll,
                        points=points,
                        parallel=3,
                        wait=True  # wait for all points to be uploaded
                    )
                    logger.info(f"Injected {len(points)} points into '{coll}' using '{dense_vector_name}' (attempt {attempt}).")
                    return  # success

                except Exception as e:
                    logger.warning({
                        "message": "Qdrant upload failed, retrying",
                        "attempt": attempt,
                        "max": MAX_RETRIES,
                        "error": str(e),
                    })
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(2 ** attempt)   # exponential backoff: 2s, 4s

        except Exception as e:
            logger.error({"message": "Failed to inject data into Qdrant", "error": str(e)})
            raise
