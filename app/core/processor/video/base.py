from abc import ABC, abstractmethod


class VideoProcessor(ABC):
    @abstractmethod
    async def process(self):
        raise NotImplementedError
