from fastembed.sparse.sparse_embedding_base import SparseEmbedding
from pinecone.models.inference.embed import SparseEmbedding as pse
from .base import BaseSparseEmbedder
from app.utils.logger import logger
from pinecone import AsyncPinecone
from typing import cast
import numpy as np


class PineconeSparseEmbedder(BaseSparseEmbedder):
    def __init__(self, api_key: str, model: str = "pinecone-sparse-english-v0", timeout: float = 60 * 10, **kwargs):
        self.model = model
        self._client = AsyncPinecone(api_key=api_key, timeout=timeout, **kwargs)

    async def embed(self, text: str, **kwargs) -> SparseEmbedding:
        try:
            """
            Embeds a single string and returns a SparseEmbedding.
            """
            # Simply pass it as a batch of 1 to reuse embed_batch logic
            results = await self.embed_batch([text], **kwargs)
            return results[0]
        except Exception as e:
            logger.error({"message": "Failed to embed text via Pinecone", "error": str(e)})
            raise e

    async def embed_batch(self, texts: list[str], **kwargs) -> list[SparseEmbedding]:
        try:
            """
            Embeds a batch of strings and returns a list of SparseEmbeddings.
            Optional kwargs:
            - input_type (str): "passage" (default) or "query"
            - truncate (str): "END" (default)
            - return_tokens (bool): False (default)
            """
            parameters = {
                "input_type": kwargs.get("input_type", "passage"),
                "truncate": kwargs.get("truncate", "END"),
                "return_tokens": kwargs.get("return_tokens", False)
            }
            response = await self._client.inference.embed(
                model=self.model,
                inputs=texts,
                parameters=parameters
            )
            sparse_embeddings = []
            for item in response.data:
                item_any = cast(pse, item)

                embedding = SparseEmbedding(
                    indices=np.array(item_any.sparse_indices),
                    values=np.array(item_any.sparse_values)
                )

                sparse_embeddings.append(embedding)

            return sparse_embeddings

        except Exception as e:
            logger.error({"message": "Failed to embed text via Pinecone", "error": str(e)})
            raise e
