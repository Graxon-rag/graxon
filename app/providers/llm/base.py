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
