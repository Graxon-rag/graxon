from ..schemas.chunk_schema import ChunkDenseVectorScore
from ..databases.qdrant.client import GQdrantClient
from app.utils.logger import logger
from qdrant_client import models
from app.config.env import Env
from typing import cast
import numpy as np
import uuid


class QdrantSimilarity:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.qdrant_client = GQdrantClient.get_client()
        logger.info("Qdrant Similarity initialized.")

    async def get_similar_chunks(
        self,
        model_key: str,
        document_id: uuid.UUID,
        chunk_ids: list[str],
        top_k: int = 3,
    ) -> dict[str, list[ChunkDenseVectorScore]]:
        try:
            coll, dense_vector_name = GQdrantClient._get_collection_vector_name(model_key)

            # Fetch ALL chunks for this project_id + document_id
            all_points, _ = await self.qdrant_client.scroll(
                collection_name=coll,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="project_id",
                            match=models.MatchValue(value=str(self.project_id)),
                        ),
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=str(document_id)),
                        ),
                    ]
                ),
                with_vectors=[dense_vector_name],
                with_payload=True,
                limit=Env.MAX_CHUNKS,
            )  # scroll returns (points, next_page_offset)

            if not all_points:
                logger.warning("No points found for given project_id and document_id.")
                return {}

            # Build pool: chunk_id → (index, dense_vector)
            pool_chunk_ids: list[str] = []
            pool_vectors: list[list[float]] = []

            for point in all_points:
                payload = point.payload

                if payload is None:
                    logger.warning(f"Skipping point {point.id} — missing payload.")
                    continue

                cid = payload.get("chunk_id")
                raw_vector = point.vector
                if isinstance(raw_vector, dict):
                    vec = raw_vector.get(dense_vector_name)
                else:
                    vec = raw_vector  # fallback if it's a plain list

                if cid is None or vec is None:
                    logger.warning(f"Skipping point {point.id} — missing chunk_id or dense vector.")
                    continue

                if not isinstance(vec, list):
                    logger.warning(f"Skipping point {point.id} — unexpected vector type: {type(vec)}")
                    continue

                dense_vec: list[float] = cast(list[float], vec)
                pool_chunk_ids.append(cid)
                pool_vectors.append(dense_vec)

            if not pool_vectors:
                logger.warning("Pool is empty after filtering.")
                return {}

            # Normalize pool matrix for cosine similarity
            pool_matrix = np.array(pool_vectors, dtype=np.float32)           # (N, D)
            norms = np.linalg.norm(pool_matrix, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1e-10, norms)                       # avoid division by zero
            pool_matrix_normalized = pool_matrix / norms                      # (N, D) unit vectors

            pool_index = {cid: idx for idx, cid in enumerate(pool_chunk_ids)}

            # For each source chunk_id compute top-k similar chunks
            result: dict[str, list[ChunkDenseVectorScore]] = {}

            for source_chunk_id in chunk_ids:
                if source_chunk_id not in pool_index:
                    logger.warning(f"chunk_id={source_chunk_id} not found in pool, skipping.")
                    result[source_chunk_id] = []
                    continue

                src_idx = pool_index[source_chunk_id]
                src_vec = pool_matrix_normalized[src_idx]                    # (D,)

                # Cosine similarity against entire pool
                scores = pool_matrix_normalized @ src_vec                    # (N,)

                # Exclude self
                scores[src_idx] = -np.inf

                # Top-k indices
                top_indices = np.argsort(scores)[::-1][:top_k]

                result[source_chunk_id] = [
                    ChunkDenseVectorScore(
                        chunk_id=pool_chunk_ids[i],
                        score=float(round(scores[i], 6)),
                    )
                    for i in top_indices
                    if scores[i] > -np.inf
                ]

                logger.info(f"chunk_id={source_chunk_id} → top {top_k} neighbors found.")

            return result

        except Exception as e:
            logger.error({"message": "Failed to compute chunk similarity", "error": str(e)})
            raise
