from abc import ABC, abstractmethod


class BaseEmbedder(ABC):

    @abstractmethod
    async def aembed(self, text: str) -> list[float]:
        """
        Asynchronous embed
        """
        raise NotImplementedError
