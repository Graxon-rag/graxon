from qdrant_client.models import Filter, FieldCondition, MatchValue, Condition, Prefetch, SparseVector, FusionQuery, Fusion
from fastembed import SparseEmbedding
from typing import List, Optional
import uuid

from ..databases.qdrant.client import GQdrantClient
from app.utils.logger import logger


class QDrantRetrieval:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id

    async def retrieve(
        self,
        model_key: str,
        query_dense_embedding: list[float],
        query_sparse_embedding: SparseEmbedding,
        top_k: int = 10,
        document_id: Optional[uuid.UUID] = None,
    ):
        try:
            coll, dense_vector_name = GQdrantClient._get_collection_vector_name(model_key)
            client = GQdrantClient.get_client()

            must_conditions: List[Condition] = [
                FieldCondition(key="org_id", match=MatchValue(value=self.org_id)),
                FieldCondition(key="project_id", match=MatchValue(value=str(self.project_id))),
            ]

            if document_id is not None:
                must_conditions.append(
                    FieldCondition(key="document_id", match=MatchValue(value=str(document_id)))
                )

            query_filter = Filter(must=must_conditions)

            results = await client.query_points(
                collection_name=coll,
                prefetch=[
                    Prefetch(
                        query=query_dense_embedding,
                        limit=top_k,
                        using=dense_vector_name,
                    ),
                    Prefetch(
                        query=SparseVector(
                            indices=query_sparse_embedding.indices.tolist(),
                            values=query_sparse_embedding.values.tolist(),
                        ),
                        limit=top_k,
                        using="sparse",
                    ),
                ],
                query=FusionQuery(fusion=Fusion.RRF),
                query_filter=query_filter,
                limit=top_k,
            )

            return results

        except Exception as e:
            logger.error({"message": "Failed to retrieve", "error": str(e)})
            raise e
