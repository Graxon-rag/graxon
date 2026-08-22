from langchain_core.runnables import Runnable
from abc import ABC, abstractmethod
from typing import Any, Union, Type
from pydantic import BaseModel


class BaseLLM(ABC):

    @abstractmethod
    async def ainvoke(self, prompt: str) -> Any:
        """
        Asynchronous invoke
        """
        # result will be an AIMessage OR the Pydantic object if structured
        raise NotImplementedError

    @abstractmethod
    def with_structured_output(self, schema: Union[Type[BaseModel], dict]) -> "BaseLLM":
        """
        Wraps the underlying LLM with structured output capabilities.
        Note: This returns a modified instance or a new one.
        """
        raise NotImplementedError

    @abstractmethod
    def get_langchain_llm(self) -> Runnable:
        """
        Returns the underlying LangChain LLM (or the structured runnable if bound).
        Useful for native LangChain operations like .stream(), .batch(), or LCEL.
        """
        raise NotImplementedError
