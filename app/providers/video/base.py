from abc import ABC, abstractmethod


class VideoProvider(ABC):

    @abstractmethod
    async def client(self):
        raise NotImplementedError
