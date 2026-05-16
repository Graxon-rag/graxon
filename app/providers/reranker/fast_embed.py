from fastembed.rerank.cross_encoder import TextCrossEncoder
from langchain_core.documents import Document
from app.utils.logger import logger
from .base import BaseReranker


class FastEmbedReranker(BaseReranker):
    def __init__(self, rerank_model: str = "jinaai/jina-reranker-v1-turbo-en", **kwargs):
        print("Loading FastEmbed models........")

        self._reranker = TextCrossEncoder(rerank_model, cache_dir=".fastembed_cache", **kwargs)

        print("FastEmbed models loaded")

    def rerank(self, query: str, docs: list[Document], top_k: int = 10, **kwargs) -> list[Document]:
        try:
            if not docs:
                return []

            doc_texts = [doc.page_content for doc in docs]

            # Rerank returns scores for each (query, document) pair
            rerank_results = list(self._reranker.rerank(query, documents=doc_texts, **kwargs))

            # rerank_results is a list of scores (floats) aligned with doc_texts
            scored_docs = sorted(
                zip(rerank_results, docs),
                key=lambda x: x[0],
                reverse=True
            )

            top_docs = [doc for _, doc in scored_docs[:top_k]]
            return top_docs

        except Exception as e:
            logger.error({"message": "Failed to rerank documents", "error": str(e)})
            raise e
