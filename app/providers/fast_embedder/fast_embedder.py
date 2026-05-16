from fastembed.text.text_embedding import TextEmbedding
from app.utils.logger import logger
from .base import BaseFastEmbedEmbedder


class FastEmbedEmbedder(BaseFastEmbedEmbedder):
    def __init__(self, model: str = "nomic-ai/nomic-embed-text-v1", **kwargs):
        print("Loading FastEmbed models........")

        self._embedder = TextEmbedding(model_name=model, cache_dir=".fastembed_cache", **kwargs)

        print("FastEmbed models loaded")

    async def embed(self, text: str, **kwargs) -> list[float]:
        try:
            embeddings = list(self._embedder.embed([text]))
            return embeddings[0].tolist()

        except Exception as e:
            logger.error({
                "message": "Failed to embed text via FastEmbed",
                "error": str(e),
            })
            raise

    async def embed_batch(self, texts: list[str], **kwargs) -> list[list[float]]:
        try:
            embeddings = self._embedder.embed(texts)

            return [embedding.tolist() for embedding in embeddings]

        except Exception as e:
            logger.error({
                "message": "Failed to embed batch via FastEmbed",
                "error": str(e),
            })
            raise e
