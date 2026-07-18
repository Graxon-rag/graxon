from twelvelabs import AsyncTwelveLabs
from .base import VideoProvider


class TwelveLabsVideoProvider(VideoProvider):
    def __init__(self, api_key: str):
        self._client = AsyncTwelveLabs(api_key=api_key)

    async def client(self):
        return self._client
