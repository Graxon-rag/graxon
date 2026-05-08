from ..provider import WorkflowEmbedder, WorkflowSparseEmbedder
from ..schemas.provider_schema import QueryProviderSchema
from app.core.qdrant.retrieval import QDrantRetrieval
from langgraph.graph import StateGraph, START, END
from fastembed import SparseEmbedding
from typing import TypedDict, Annotated
from langgraph.types import Send
from app.utils.logger import logger
import operator
import uuid

SUPERVISOR_AGENT = "supervisor_agent"
QUERY_EXPANSION_AGENT = "query_expansion_agent"
EMBEDDING_AGENT = "embedding_agent"
SPARSE_EMBEDDING_AGENT = "sparse_embedding_agent"
VECTOR_DATABASE_AGENT = "vector_database_agent"
GRAPH_DATABASE_AGENT = "graph_database_agent"
RERANKER_AGENT = "reranker_agent"
ANSWER_AGENT = "answer_agent"


def merge_optional(a, b):
    return b if b is not None else a


class DQGState(TypedDict):
    request_id: str
    org_id: str
    project_id: uuid.UUID
    providers: QueryProviderSchema
    query: str
    top_k: int

    queries: list[str] | None
    document_id: uuid.UUID | None
    model_key: Annotated[str | None, merge_optional]
    query_dense_embedding: Annotated[list[float] | None, merge_optional]
    query_sparse_embedding: Annotated[SparseEmbedding | None, merge_optional]

    answer: str | dict | None


class DocumentQueryGraph():
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.q_retrieval = QDrantRetrieval(org_id=org_id, project_id=project_id)

    def build_graph(self):
        try:
            graph = StateGraph(DQGState)

            # Add nodes
            graph.add_node(SUPERVISOR_AGENT, self._supervisor)
            graph.add_node(QUERY_EXPANSION_AGENT, self._query_expansion)
            graph.add_node(EMBEDDING_AGENT, self._embedding)
            graph.add_node(SPARSE_EMBEDDING_AGENT, self._sparse_embedding)
            graph.add_node(VECTOR_DATABASE_AGENT, self._vector_database)
            graph.add_node(GRAPH_DATABASE_AGENT, self._graph_database)
            graph.add_node(RERANKER_AGENT, self._reranker)
            graph.add_node(ANSWER_AGENT, self._answer)

            # Add edges
            graph.add_edge(START, SUPERVISOR_AGENT)
            graph.add_edge(SUPERVISOR_AGENT, QUERY_EXPANSION_AGENT)

            # Fan-out: trigger both in parallel after query expansion
            graph.add_conditional_edges(
                QUERY_EXPANSION_AGENT,
                self._fan_out_embeddings,   # <-- router function
                [EMBEDDING_AGENT, SPARSE_EMBEDDING_AGENT]
            )

            # Fan-in: both converge into vector DB
            graph.add_edge(EMBEDDING_AGENT, VECTOR_DATABASE_AGENT)
            graph.add_edge(SPARSE_EMBEDDING_AGENT, VECTOR_DATABASE_AGENT)

            graph.add_edge(VECTOR_DATABASE_AGENT, GRAPH_DATABASE_AGENT)
            graph.add_edge(GRAPH_DATABASE_AGENT, RERANKER_AGENT)
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
    def _fan_out_embeddings(self, state: DQGState) -> list[str]:
        return [EMBEDDING_AGENT, SPARSE_EMBEDDING_AGENT]

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

            model_key = self._get_model_key(embedder_provider.value, dimension)
            return {"query_dense_embedding": embedding, "model_key": model_key}

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

            result = await self.q_retrieval.retrieve(model_key=model_key, query_sparse_embedding=query_sparse_embedding, query_dense_embedding=query_dense_embedding, top_k=top_k, document_id=document_id)
            result = result.model_dump(mode="json")
            return {"answer": result}

        except Exception as e:
            logger.error({"message": "Failed to vector database", "error": str(e)})
            raise e

    async def _graph_database(self, state: DQGState):
        try:
            pass
        except Exception as e:
            logger.error({"message": "Failed to graph database", "error": str(e)})
            raise e

    async def _reranker(self, state: DQGState):
        try:
            pass
        except Exception as e:
            logger.error({"message": "Failed to reranker", "error": str(e)})
            raise e

    async def _answer(self, state: DQGState):
        try:
            pass
        except Exception as e:
            logger.error({"message": "Failed to answer", "error": str(e)})
            raise e

    def _get_model_key(self, provider: str, dimension: int) -> str:
        return f"{provider}_{dimension}"
