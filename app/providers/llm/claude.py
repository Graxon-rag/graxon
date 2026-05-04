from langchain_anthropic import ChatAnthropic
from app.utils.logger import logger
from typing import Type, Union, Any
from pydantic import SecretStr, BaseModel
from .base import BaseLLM


class ClaudeLLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5", timeout: float = 60, stop: Any = None, **kwargs):
        if not api_key:
            raise ValueError("Claude API key is required")

        self._raw_llm = ChatAnthropic(api_key=SecretStr(api_key), model_name=model, timeout=timeout, stop=stop, model_kwargs=kwargs)
        self._llm = self._raw_llm

    def with_structured_output(self, schema: Union[Type[BaseModel], dict]) -> "ClaudeLLM":
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
            logger.error({"message": "Failed to complete Claude LLM", "error": str(e)})
            raise e
