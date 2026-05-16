from abc import ABC, abstractmethod
from app.utils.logger import logger


class BaseFastEmbedEmbedder(ABC):

    @abstractmethod
    async def embed(self, text: str, **kwargs) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    async def embed_batch(self, texts: list[str], **kwargs) -> list[list[float]]:
        raise NotImplementedError
