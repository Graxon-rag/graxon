from abc import ABC, abstractmethod


class AudioProvider(ABC):
    @abstractmethod
    async def client(self):
        raise NotImplementedError
