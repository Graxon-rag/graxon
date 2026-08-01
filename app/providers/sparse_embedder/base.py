from fastembed.sparse.sparse_embedding_base import SparseEmbedding
from abc import ABC, abstractmethod


class BaseSparseEmbedder(ABC):
    @abstractmethod
    async def embed(self, text: str, **kwargs) -> SparseEmbedding:
        raise NotImplementedError

    @abstractmethod
    async def embed_batch(self, texts: list[str], **kwargs) -> list[SparseEmbedding]:
        raise NotImplementedError
