from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from app.utils.logger import logger
from pydantic import SecretStr, BaseModel
from typing import Type, Union, Any


class GeminiEmbedding:
    def __init__(self, api_key: str, model: str = "gemini-embedding-001", **kwargs):
        if not api_key:
            raise ValueError("Gemini API key is required")

        self._raw_llm = GoogleGenerativeAIEmbeddings(api_key=SecretStr(api_key), model=model, **kwargs)
        self._llm = self._raw_llm
