from app.core.schemas.chunk_schema import ChunkQuerySchema, ChunkPrevNextVecSimilarity
from ..schemas.provider_schema import QueryProviderSchema, LLMProviderSchema
from qdrant_client.conversions.common_types import QueryResponse
from ..provider import WorkflowEmbedder, WorkflowSparseEmbedder
from app.core.qdrant.retrieval import QDrantRetrieval
from ..provider import WorkflowReranker, WorkflowLLM
from langgraph.graph import StateGraph, START, END
from .prompts.answer_prompt import ANSWER_PROMPT
from app.core.schemas import query_schema as qs
from langchain_core.documents import Document
from typing import TypedDict, Annotated, List
from qdrant_client.models import ScoredPoint
from app.core.neo4j.chunk import GN4jChunk
from fastembed import SparseEmbedding
from app.utils.logger import logger
from langgraph.types import Send
from app.config.env import Env
import uuid

SUPERVISOR_AGENT = "supervisor_agent"
QUERY_EXPANSION_AGENT = "query_expansion_agent"
EMBEDDING_AGENT = "embedding_agent"
SPARSE_EMBEDDING_AGENT = "sparse_embedding_agent"
VECTOR_DATABASE_AGENT = "vector_database_agent"
QUICK_QUERY_AGENT = "quick_query_agent"
SMART_QUERY_AGENT = "smart_query_agent"
EXPERT_QUERY_AGENT = "expert_query_agent"
RERANKER_AGENT = "reranker_agent"
ANSWER_AGENT = "answer_agent"


def merge_optional(a, b):
    return b if b is not None else a


class DQGState(TypedDict):
    request_id: str
    org_id: str
    project_id: uuid.UUID
    providers: QueryProviderSchema
    model_key: str
    query: str
    top_k: int
    query_type: qs.QueryType
    query_depth: qs.QueryDepth

    queries: list[str] | None
    document_id: uuid.UUID | None
    points: list[ScoredPoint] | None
    chunks: list[ChunkQuerySchema] | None
    reranked_chunks: list[ChunkQuerySchema] | None
    query_dense_embedding: Annotated[list[float] | None, merge_optional]
    query_sparse_embedding: Annotated[SparseEmbedding | None, merge_optional]

    answer: str | dict | None


class DocumentQueryGraph():
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.q_retrieval = QDrantRetrieval(org_id=org_id, project_id=project_id)
        self._chunk_n4j = GN4jChunk(org_id=org_id, project_id=project_id)

    def build_graph(self):
        try:
            graph = StateGraph(DQGState)

            # Add nodes
            graph.add_node(SUPERVISOR_AGENT, self._supervisor)
            graph.add_node(QUERY_EXPANSION_AGENT, self._query_expansion)
            graph.add_node(EMBEDDING_AGENT, self._embedding)
            graph.add_node(SPARSE_EMBEDDING_AGENT, self._sparse_embedding)
            graph.add_node(VECTOR_DATABASE_AGENT, self._vector_database)
            graph.add_node(QUICK_QUERY_AGENT, self._quick_query)
            graph.add_node(SMART_QUERY_AGENT, self._smart_query)
            graph.add_node(EXPERT_QUERY_AGENT, self._expert_query)

            graph.add_node(RERANKER_AGENT, self._reranker)
            graph.add_node(ANSWER_AGENT, self._answer)

            # Add edges
            graph.add_edge(START, SUPERVISOR_AGENT)
            graph.add_edge(SUPERVISOR_AGENT, QUERY_EXPANSION_AGENT)

            # Fan-out: trigger both in parallel after query expansion
            graph.add_conditional_edges(
                QUERY_EXPANSION_AGENT,
                self._fan_out_embeddings,
                [EMBEDDING_AGENT, SPARSE_EMBEDDING_AGENT]
            )

            # Fan-in: both converge into vector DB
            graph.add_edge(EMBEDDING_AGENT, VECTOR_DATABASE_AGENT)
            graph.add_edge(SPARSE_EMBEDDING_AGENT, VECTOR_DATABASE_AGENT)

            graph.add_conditional_edges(
                VECTOR_DATABASE_AGENT,
                self._routing_by_query_type,
                {
                    "quick": QUICK_QUERY_AGENT,
                    "smart": SMART_QUERY_AGENT,
                    "expert": EXPERT_QUERY_AGENT
                }
            )

            graph.add_edge(QUICK_QUERY_AGENT, RERANKER_AGENT)
            graph.add_edge(SMART_QUERY_AGENT, RERANKER_AGENT)
            graph.add_edge(EXPERT_QUERY_AGENT, RERANKER_AGENT)
            graph.add_edge(RERANKER_AGENT, ANSWER_AGENT)
            graph.add_edge(ANSWER_AGENT, END)

            workflow = graph.compile()
            mermaid = workflow.get_graph().draw_mermaid()
            print(mermaid)
            logger.info({"message": "Query Graph built successfully"})

            return workflow
        except Exception as e:
            logger.error({"message": "Failed to build graph", "error": str(e)})
            raise e

    # -- Router: fans out to BOTH nodes simultaneously --
    def _fan_out_embeddings(self, state: DQGState) -> list[Send]:
        return [
            Send(EMBEDDING_AGENT, state),
            Send(SPARSE_EMBEDDING_AGENT, state),
        ]

    def _routing_by_query_type(self, state: DQGState):
        query_type = state["query_type"]
        if query_type is qs.QueryType.QUICK:
            return "quick"
        elif query_type is qs.QueryType.SMART:
            return "smart"
        elif query_type is qs.QueryType.EXPERT:
            return "expert"
        else:
            raise Exception(f"Unknown query type: {query_type}")    

    async def _supervisor(self, state: DQGState):
        try:
            query = state["query"]
            if query is None or query == "" or query.strip() == "":
                raise Exception("Query is None")

            new_query = query.strip()

            top_k = state["top_k"]
            if top_k is None or top_k == 0:
                top_k = 10

            return {
                "queries": [new_query],
                "top_k": top_k,
            }
        except Exception as e:
            logger.error({"message": "Failed to supervisor", "error": str(e)})
            raise e

    async def _query_expansion(self, state: DQGState):
        try:
            # TODO: implement query expansion
            pass
        except Exception as e:
            logger.error({"message": "Failed to query expansion", "error": str(e)})
            raise e

    async def _embedding(self, state: DQGState):
        try:
            # TODO: make this multi query
            providers = state["providers"]
            queries = state["queries"]
            query = state["query"]
            first_query = queries[0] if queries is not None and len(queries) > 0 else query.strip()

            embedder_provider = providers.embedding.provider
            api_key = providers.embedding.api_key
            model = providers.embedding.model
            dimension = providers.embedding.dimension

            embedder = WorkflowEmbedder.embedder(provider=embedder_provider, api_key=api_key, model=model, dimension=dimension)
            embedding = await embedder.aembed(first_query)

            return {"query_dense_embedding": embedding}

        except Exception as e:
            logger.error({"message": "Failed to embedding", "error": str(e)})
            raise e

    async def _sparse_embedding(self, state: DQGState):
        try:
            # TODO: make this multi query
            providers = state["providers"]
            queries = state["queries"]
            query = state["query"]
            first_query = queries[0] if queries is not None and len(queries) > 0 else query.strip()
            sparse_provider = providers.sparse_model.provider
            sparse_model = providers.sparse_model.model

            sparse_embedder = WorkflowSparseEmbedder.sparse_embedder(model=sparse_model, provider=sparse_provider)
            em_vector: SparseEmbedding = sparse_embedder.embed(first_query)
            return {"query_sparse_embedding": em_vector}
        except Exception as e:
            logger.error({"message": "Failed to sparse embedding", "error": str(e)})
            raise e

    async def _vector_database(self, state: DQGState):
        try:
            query_sparse_embedding = state["query_sparse_embedding"]
            query_dense_embedding = state["query_dense_embedding"]
            top_k = state["top_k"]
            document_id = state["document_id"]
            model_key = state["model_key"]

            if model_key is None:
                raise Exception("Model key is None")
            if query_sparse_embedding is None:
                raise Exception("Query sparse embedding is None")
            if query_dense_embedding is None:
                raise Exception("Query dense embedding is None")

            result: QueryResponse = await self.q_retrieval.retrieve(model_key=model_key, query_sparse_embedding=query_sparse_embedding, query_dense_embedding=query_dense_embedding, top_k=top_k, document_id=document_id)
            return {"points": result.points}

        except Exception as e:
            logger.error({"message": "Failed to vector database", "error": str(e)})
            raise e

    async def _quick_query(self, state: DQGState):
        try:
            logger.info({"message": "Quick query"})
            points = state["points"]

            if points is None or len(points) == 0:
                raise Exception("No points found")

            chunks: list[ChunkQuerySchema] = []
            for point in points:
                payload = point.payload
                if payload is None:
                    continue

                text = payload.get("text")
                chunk_id = payload.get("chunk_id")
                if text is None or chunk_id is None:
                    continue

                chunks.append(ChunkQuerySchema(chunk_id=chunk_id, text=text, weight=point.score))

            return {"chunks": chunks}
        except Exception as e:
            logger.error({"message": "Failed in quick query", "error": str(e)})

    async def _smart_query(self, state: DQGState):
        try:
            logger.info({"message": "Smart query"})
            points = state["points"]

            if points is None or len(points) == 0:
                raise Exception("No points found")
            document_id = state["document_id"]
            chunk_ids: list[str] = [
                chunk_id
                for p in points
                if p.payload is not None and (chunk_id := p.payload.get("chunk_id")) is not None
            ]
            prev_next_vector_similar_chunks: List[ChunkPrevNextVecSimilarity] = await self._chunk_n4j.get_prev_next_vector_similar_chunks(chunk_ids=chunk_ids, gte__vector_score=Env.GTE_VECTOR_SIMILAR, document_id=document_id)

            chunks: list[ChunkQuerySchema] = []
            for c in prev_next_vector_similar_chunks:
                prev_chunk_id = c.prev_chunk.chunk_id if c.prev_chunk is not None else None
                prev_chunk_text = c.prev_chunk.text if c.prev_chunk is not None else None
                prev_chunk_weight = c.prev_chunk.weight if c.prev_chunk is not None else None

                next_chunk_id = c.next_chunk.chunk_id if c.next_chunk is not None else None
                next_chunk_text = c.next_chunk.text if c.next_chunk is not None else None
                next_chunk_weight = c.next_chunk.weight if c.next_chunk is not None else None

                if prev_chunk_id is not None and prev_chunk_text is not None and prev_chunk_weight is not None:
                    chunks.append(ChunkQuerySchema(chunk_id=prev_chunk_id, text=prev_chunk_text, weight=prev_chunk_weight))
                if next_chunk_id is not None and next_chunk_text is not None and next_chunk_weight is not None:
                    chunks.append(ChunkQuerySchema(chunk_id=next_chunk_id, text=next_chunk_text, weight=next_chunk_weight))

                for vs_chunk in c.vector_similar_chunks or []:
                    chunks.append(ChunkQuerySchema(chunk_id=vs_chunk.chunk_id, text=vs_chunk.text, weight=vs_chunk.weight))

            # Find unique chunks
            unique_chunk_ids: list[str] = []
            unique_chunks: list[ChunkQuerySchema] = []

            for chunk in chunks:
                if chunk.chunk_id not in unique_chunk_ids:
                    unique_chunk_ids.append(chunk.chunk_id)
                    unique_chunks.append(chunk)

            return {"chunks": unique_chunks}
        except Exception as e:
            logger.error({"message": "Failed in smart query", "error": str(e)})

    async def _expert_query(self, state: DQGState):
        try:
            logger.info({"message": "Expert query"})
        except Exception as e:
            logger.error({"message": "Failed in expert query", "error": str(e)})

    async def _reranker(self, state: DQGState):
        try:
            query = state["query"]
            chunks = state["chunks"]
            top_k = state["top_k"]

            if chunks is None or len(chunks) == 0:
                raise Exception("No chunks found")
            providers = state["providers"]
            reranker_provider = providers.reranker.provider
            reranker_model = providers.reranker.model

            reranker = WorkflowReranker().reranker(model=reranker_model, provider=reranker_provider)

            docs: list[Document] = []
            for chunk in chunks:
                docs.append(Document(page_content=chunk.text, metadata={"chunk_id": chunk.chunk_id}))

            rerank_docs = reranker.rerank(query=query, docs=docs, top_k=top_k)

            reranked_chunks: list[ChunkQuerySchema] = []
            for doc in rerank_docs:
                reranked_chunks.append(ChunkQuerySchema(chunk_id=doc.metadata["chunk_id"], text=doc.page_content, weight=1.0))

            return {"reranked_chunks": reranked_chunks}
        except Exception as e:
            logger.error({"message": "Failed to reranker", "error": str(e)})
            raise e

    async def _answer(self, state: DQGState):
        try:
            reranked_chunks = state["reranked_chunks"]
            if reranked_chunks is None or len(reranked_chunks) == 0:
                raise Exception("No reranked chunks found")

            query = state["query"]
            providers = state["providers"]
            llm_provider = providers.llm

            answer = await self._llm_call(query=query, provider=llm_provider, reranked_chunks=reranked_chunks)

            return {"answer": answer}
        except Exception as e:
            logger.error({"message": "Failed to answer", "error": str(e)})
            raise e

    async def _llm_call(self, query: str, provider: LLMProviderSchema, reranked_chunks: list[ChunkQuerySchema]) -> str:
        try:
            llm_provider = provider.provider
            api_key = provider.api_key
            model = provider.model
            chunks_str = self._format_chunks(reranked_chunks)

            prompt = ANSWER_PROMPT.format(context=chunks_str, query=query)
            llm = WorkflowLLM.llm(provider=llm_provider, api_key=api_key, model=model)
            response = await llm.ainvoke(prompt=prompt)

            return response.content
        except Exception as e:
            logger.error({"message": "Failed to llm call", "error": str(e)})
            raise e

    def _format_chunks(self, chunks: list[ChunkQuerySchema]) -> str:
        return "\n\n".join(
            f"[Chunk {i + 1}]:\n{chunk.text}"
            for i, chunk in enumerate(chunks)
        )
