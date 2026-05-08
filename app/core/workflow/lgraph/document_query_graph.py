from ..schemas.provider_schema import QueryProviderSchema
from langgraph.graph import StateGraph, START, END
from fastembed import SparseEmbedding
from app.utils.logger import logger
from typing import TypedDict
import uuid

SUPERVISOR_AGENT = "supervisor_agent"
QUERY_PARSER_AGENT = "query_parser_agent"
EMBEDDING_AGENT = "embedding_agent"
SPARSE_EMBEDDING_AGENT = "sparse_embedding_agent"
VECTOR_DATABASE_AGENT = "vector_database_agent"
GRAPH_DATABASE_AGENT = "graph_database_agent"


class DQGState(TypedDict):
    request_id: str
    org_id: str
    project_id: uuid.UUID
    providers: QueryProviderSchema
    query: str
    top_k: int

    document_id: uuid.UUID | None
    query_dense_embedding: list[float] | None
    query_sparse_embedding: SparseEmbedding | None


class DocumentQueryGraph():
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id

    def build_graph(self):
        try:
            graph = StateGraph(DQGState)

            # Add nodes
            graph.add_node(SUPERVISOR_AGENT, self._supervisor)
            graph.add_node(QUERY_PARSER_AGENT, self._query_parser)
            graph.add_node(EMBEDDING_AGENT, self._embedding)
            graph.add_node(SPARSE_EMBEDDING_AGENT, self._sparse_embedding)
            graph.add_node(VECTOR_DATABASE_AGENT, self._vector_database)
            graph.add_node(GRAPH_DATABASE_AGENT, self._graph_database)

            # Add edges
            graph.add_edge(START, SUPERVISOR_AGENT)
            graph.add_edge(SUPERVISOR_AGENT, QUERY_PARSER_AGENT)

            graph.add_edge(QUERY_PARSER_AGENT, EMBEDDING_AGENT)
            graph.add_edge(QUERY_PARSER_AGENT, SPARSE_EMBEDDING_AGENT)

            graph.add_edge(EMBEDDING_AGENT, VECTOR_DATABASE_AGENT)
            graph.add_edge(SPARSE_EMBEDDING_AGENT, VECTOR_DATABASE_AGENT)

            graph.add_edge(VECTOR_DATABASE_AGENT, GRAPH_DATABASE_AGENT)

            graph.add_edge(GRAPH_DATABASE_AGENT, END)

            workflow = graph.compile()
            mermaid = workflow.get_graph().draw_mermaid()
            print(mermaid)
            logger.info({"message": "Query Graph built successfully"})

            return workflow
        except Exception as e:
            logger.error({"message": "Failed to build graph", "error": str(e)})
            raise e

    async def _supervisor(self, state: DQGState):
        try:
            pass
        except Exception as e:
            logger.error({"message": "Failed to supervisor", "error": str(e)})
            raise e

    async def _query_parser(self, state: DQGState):
        try:
            pass
        except Exception as e:
            logger.error({"message": "Failed to query parser", "error": str(e)})
            raise e

    async def _embedding(self, state: DQGState):
        try:
            pass
        except Exception as e:
            logger.error({"message": "Failed to embedding", "error": str(e)})
            raise e

    async def _sparse_embedding(self, state: DQGState):
        try:
            pass
        except Exception as e:
            logger.error({"message": "Failed to sparse embedding", "error": str(e)})
            raise e

    async def _vector_database(self, state: DQGState):
        try:
            pass
        except Exception as e:
            logger.error({"message": "Failed to vector database", "error": str(e)})
            raise e

    async def _graph_database(self, state: DQGState):
        try:
            pass
        except Exception as e:
            logger.error({"message": "Failed to graph database", "error": str(e)})
            raise e
