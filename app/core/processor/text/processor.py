from langchain_core.documents import Document
from abc import ABC, abstractmethod
from typing import List, Tuple


class Processor(ABC):

    @abstractmethod
    async def process(self) -> Tuple[List[Document], int, bool]:
        """
        Process the next batch of data from the input source.

        Implementations should read a portion of the source file, convert the
        extracted content into LangChain ``Document`` objects, and return them
        along with the updated chunk index and a completion flag. This allows
        large files to be processed incrementally across multiple calls.

        Returns:
            Tuple[List[Document], int, bool]:
                A tuple containing:

                - List[Document]:
                    The processed documents generated from the current batch.

                - int:
                    The next RAG chunk index to use when processing the
                    subsequent batch.

                - bool:
                    ``True`` if the entire input has been processed and no
                    further calls are required; otherwise ``False``.
        """
        pass
