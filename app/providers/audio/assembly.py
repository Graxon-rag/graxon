from .base import BaseAudioProvider
import assemblyai as aai


class AssemblyAudioProvider(BaseAudioProvider):
    def __init__(self, api_key: str):
        aai.settings.api_key = api_key
        self._client = aai

    async def client(self):
        return self._client
