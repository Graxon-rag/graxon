from langchain_core.documents import Document
from app.utils.logger import logger
from .base import BaseReranker
import httpx


class JinaReranker(BaseReranker):
    def __init__(self, api_key: str, base_url: str = "https://api.jina.ai/v1/rerank", model: str = "jina-reranker-v3", timeout: float = 60 * 10):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    async def rerank(self, query: str, docs: list[Document], top_k: int = 10, **kwargs) -> list[Document]:
        try:
            logger.info({
                "message": f"Calling Jina API for reranking {len(docs)} documents",
                "query": query,
                "top_k": top_k,
                "model": self.model
            })
            if not docs:
                return []

            doc_texts = [doc.page_content for doc in docs]

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    json={
                        "model": self.model,
                        "query": query,
                        "top_n": top_k,
                        "documents": doc_texts,
                        "return_documents": False,  # Setting to False means Jina only returns indices
                    },
                )
                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                if not results:
                    logger.warning({"message": "Jina rerank returned no results, falling back"})
                    return []

                logger.info({"message": "Jina rerank returned results", "results": len(results)})

                reranked = []
                for r in results:
                    idx = r.get("index")
                    if idx is None or idx >= len(docs):
                        continue

                    # Fetch the original Langchain Document as it is
                    doc = docs[idx]

                    # Optional but recommended: Add the Cohere score to the document's metadata
                    doc.metadata["rerank_relevance_score"] = r.get("relevance_score", 0.0)
                    reranked.append(doc)

                return reranked
        except Exception as e:
            logger.error({"message": "Failed to rerank documents", "error": str(e)})
            raise e
