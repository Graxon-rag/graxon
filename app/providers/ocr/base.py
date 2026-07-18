from abc import ABC, abstractmethod


class OCRProvider(ABC):
    @abstractmethod
    async def client(self):
        raise NotImplementedError
