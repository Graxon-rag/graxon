from typing import Type, Union, Any
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import AIMessage
from pydantic import SecretStr, BaseModel
from app.utils.logger import logger
from .base import BaseLLM


class DeepseekLLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "deepseek-chat", **kwargs):
        if not api_key:
            raise ValueError("Deepseek API key is required")

        # We keep the base LLM and a "runnable" version that can be modified
        self._raw_llm = ChatDeepSeek(api_key=SecretStr(api_key), model=model, **kwargs)
        self._llm = self._raw_llm

    def with_structured_output(self, schema: Union[Type[BaseModel], dict]) -> "DeepseekLLM":
        """
        Wraps the underlying LLM with structured output capabilities.
        Note: This returns a modified instance or a new one.
        """
        try:
            # We update self._llm to be the structured version
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
            logger.error({"message": "Failed to complete Deepseek LLM", "error": str(e)})
            raise e
