from langchain_google_genai import ChatGoogleGenerativeAI
from app.utils.logger import logger
from pydantic import SecretStr, BaseModel
from typing import Type, Union, Any
from .base import BaseLLM


class GeminiLLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", **kwargs):
        if not api_key:
            raise ValueError("Gemini API key is required")

        self._raw_llm = ChatGoogleGenerativeAI(api_key=SecretStr(api_key), model=model, **kwargs)
        self._llm = self._raw_llm

    def with_structured_output(self, schema: Union[Type[BaseModel], dict]) -> "GeminiLLM":
        try:
            self._llm = self._raw_llm.with_structured_output(schema)
            return self
        except Exception as e:
            logger.error({"message": "Failed to bind structured output", "error": str(e)})
            raise e

    async def ainvoke(self, prompt: str) -> Any:
        try:
            # result will be an AIMessage OR the Pydantic object if structured
            result = await self._llm.ainvoke(prompt)
            return result
        except Exception as e:
            logger.error({"message": "Failed to complete Gemini LLM", "error": str(e)})
            raise e
