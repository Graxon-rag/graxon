from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from app.utils.logger import logger
from pydantic import SecretStr
from .base import BaseEmbedder


class GeminiEmbedder(BaseEmbedder):
    def __init__(self, api_key: str, model: str = "gemini-embedding-001", **kwargs):
        if not api_key:
            raise ValueError("Gemini API key is required")

        self._embedder = GoogleGenerativeAIEmbeddings(api_key=SecretStr(api_key), model=model, **kwargs)

    async def aembed(self, text: str, **kwargs) -> list[float]:
        try:
            return await self._embedder.aembed_query(text, **kwargs)
        except Exception as e:
            logger.error({"message": "Failed to embed text via Gemini", "error": str(e)})
            raise e
