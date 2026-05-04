from langchain_voyageai import VoyageAIEmbeddings
from app.utils.logger import logger
from pydantic import SecretStr
from .base import BaseEmbedder


class VoyageEmbedder(BaseEmbedder):
    def __init__(self, api_key: str, model: str = "voyage-4-lite", **kwargs):
        if not api_key:
            raise ValueError("Voyage API key is required")

        self._embedder = VoyageAIEmbeddings(api_key=SecretStr(api_key), model=model, **kwargs)

    async def aembed(self, text: str, **kwargs) -> list[float]:
        try:
            return await self._embedder.aembed_query(text, **kwargs)
        except Exception as e:
            logger.error({"message": "Failed to embed text via Voyage", "error": str(e)})
            raise e
