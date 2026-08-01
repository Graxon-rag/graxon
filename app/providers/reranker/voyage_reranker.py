from langchain_core.documents import Document
import voyageai.client_async as voyageai
from app.utils.logger import logger
from .base import BaseReranker


class VoyageReranker(BaseReranker):
    def __init__(self, api_key: str, model: str = "rerank-2.5", timeout: float = 60 * 10, **kwargs):
        self.model = model
        self._client = voyageai.AsyncClient(api_key=api_key, timeout=timeout, **kwargs)

    async def rerank(self, query: str, docs: list[Document], top_k: int = 10, **kwargs) -> list[Document]:
        try:
            logger.info({
                "message": f"Calling Voyage API for reranking {len(docs)} documents",
                "query": query,
                "top_k": top_k,
                "model": self.model
            })
            if not docs:
                return []

            doc_texts = [doc.page_content for doc in docs]

            response = await self._client.rerank(
                query=query,
                documents=doc_texts,
                model=self.model,
                top_k=top_k
            )

            results = response.results
            if not results:
                logger.warning({"message": "Voyage AI rerank returned no results, falling back"})
                return []

            reranked = []
            for r in results:
                idx = r.index
                if idx is None or idx >= len(docs):
                    continue

                # Fetch the original Langchain Document as it is
                doc: Document = docs[idx]

                # Optional but recommended: Add the Cohere score to the document's metadata
                doc.metadata["rerank_relevance_score"] = r.relevance_score
                reranked.append(doc)

            return reranked
        except Exception as e:
            logger.error({"message": "Failed to rerank documents", "error": str(e)})
            raise e
