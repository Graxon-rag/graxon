from langchain_core.documents import Document
from app.utils.logger import logger
from .base import BaseReranker
import cohere


class CohereReranker(BaseReranker):
    def __init__(self, api_key: str, model: str = "rerank-v3.5", timeout: float = 60 * 10, **kwargs):
        self.model = model
        self._client = cohere.AsyncClientV2(api_key=api_key, timeout=timeout, **kwargs)

    async def rerank(self, query: str, docs: list[Document], top_k: int = 10, **kwargs) -> list[Document]:
        try:
            logger.info({
                "message": f"Calling Cohere API for reranking {len(docs)} documents",
                "query": query,
                "top_k": top_k,
                "model": self.model
            })
            if not docs:
                return []

            doc_texts = [doc.page_content for doc in docs]

            response = await self._client.rerank(
                model=self.model,
                query=query,
                documents=doc_texts,
                top_n=top_k,
                **kwargs
            )

            results = response.results
            if not results:
                logger.warning({"message": "Cohere rerank returned no results, falling back"})
                return []

            reranked = []
            for r in results:
                idx = r.index
                if idx is None or idx >= len(doc_texts):
                    continue

                # Fetch the original Langchain Document as it is
                doc = docs[idx]

                # Optional but recommended: Add the Cohere score to the document's metadata
                doc.metadata["rerank_relevance_score"] = r.relevance_score
                reranked.append(doc)

            return reranked
        except Exception as e:
            logger.error({"message": "Failed to rerank documents", "error": str(e)})
            raise e
