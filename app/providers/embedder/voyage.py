from langchain_voyageai import VoyageAIEmbeddings
from app.utils.logger import logger
from pydantic import SecretStr
from typing import Literal
from .base import BaseEmbedder

VoyageDimension = Literal[256, 512, 1024, 2048]


class VoyageEmbedder(BaseEmbedder):
    def __init__(self, api_key: str, model: str = "voyage-4-lite", dimension: VoyageDimension = 1024, **kwargs):
        if not api_key:
            raise ValueError("Voyage API key is required")

        if dimension not in (1024, 2048):
            raise ValueError("Invalid Voyage dimension only supports 1024 and 2048")

        self._embedder = VoyageAIEmbeddings(api_key=SecretStr(api_key), model=model, output_dimension=dimension, **kwargs)

    async def aembed(self, text: str, **kwargs) -> list[float]:
        try:
            return await self._embedder.aembed_query(text, **kwargs)
        except Exception as e:
            logger.error({"message": "Failed to embed text via Voyage", "error": str(e)})
            raise e
