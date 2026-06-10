from langchain_core.documents import Document
from abc import ABC, abstractmethod
from typing import List, Tuple


class Processor(ABC):

    @abstractmethod
    async def process(self) -> Tuple[List[Document], int, bool]:
        pass
