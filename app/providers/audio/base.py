from abc import ABC, abstractmethod


class BaseAudioProvider(ABC):
    @abstractmethod
    async def client(self):
        raise NotImplementedError
