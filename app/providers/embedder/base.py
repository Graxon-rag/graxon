from abc import ABC, abstractmethod
from typing import Optional


class BaseEmbedder(ABC):

    @abstractmethod
    async def aembed(self, text: str) -> list[float]:
        """
        Asynchronous embed
        """
        raise NotImplementedError

    @abstractmethod
    async def aembed_batch(self, texts: list[str], batch_size: Optional[int] = None) -> list[list[float]]:
        """
        Asynchronous embed batch
        """
        raise NotImplementedError
