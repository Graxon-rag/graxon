from fastembed import SparseTextEmbedding
from fastembed.sparse.sparse_embedding_base import SparseEmbedding
from app.utils.logger import logger
from .base import BaseSparseEmbedder


class FastEmbedSparseEmbedder(BaseSparseEmbedder):

    def __init__(self, model: str = "Qdrant/bm42-all-minilm-l6-v2-attentions", **kwargs):
        print("Loading FastEmbed models........")

        self._embedder = SparseTextEmbedding(model_name=model, **kwargs)

        print("FastEmbed models loaded")

    def embed(self, text: str, **kwargs) -> SparseEmbedding:
        try:
            # Return type is SparseEmbedding — SparseTextEmbedding.embed() is a generator, so it must be consumed with list()
            result = list(self._embedder.embed(text, **kwargs))
            return result[0]
        except Exception as e:
            logger.error({"message": "Failed to embed text via FastEmbed", "error": str(e)})
            raise e

    def embed_batch(self, texts: list[str], **kwargs) -> list[SparseEmbedding]:
        try:
            # Return type is SparseEmbedding — SparseTextEmbedding.embed() is a generator, so it must be consumed with list()
            result = list(self._embedder.embed(texts, **kwargs))
            return result
        except Exception as e:
            logger.error({"message": "Failed to embed text via FastEmbed", "error": str(e)})
            raise e
