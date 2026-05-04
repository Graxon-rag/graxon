from langchain_openai.embeddings import OpenAIEmbeddings
from app.utils.logger import logger
from pydantic import SecretStr
from .base import BaseEmbedder


class OpenaiEmbedder(BaseEmbedder):
    def __init__(self, api_key: str, model: str = "text-embedding-3-large", **kwargs):
        if not api_key:
            raise ValueError("Openai API key is required")

        self._embedder = OpenAIEmbeddings(api_key=SecretStr(api_key), model=model, **kwargs)

    async def aembed(self, text: str, **kwargs) -> list[float]:
        try:
            return await self._embedder.aembed_query(text, **kwargs)
        except Exception as e:
            logger.error({"message": "Failed to embed text via Openai", "error": str(e)})
            raise e
