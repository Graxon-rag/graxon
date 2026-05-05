from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from app.core.schemas.document_schema import DocumentGetSchema
from ..schemas.provider_schema import ProviderSchema
from app.utils.logger import logger
import uuid


SUPERVISOR_AGENT = "supervisor_agent"
LLM_AGENT = "llm_agent"
EMBEDDING_AGENT = "embedding_agent"
SPARSE_AGENT = "sparse_agent"
DATABASE_AGENT = "database_agent"


class DIGState(TypedDict):
    org_id: str
    project_id: uuid.UUID
    document_id: uuid.UUID
    request_id: str
    document: DocumentGetSchema
    providers: ProviderSchema


class DocumentIngestGraph:
    def __init__(self, org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.document_id = document_id

    def build_graph(self):
        try:
            graph = StateGraph(DIGState)

            # Nodes
            graph.add_node(SUPERVISOR_AGENT, self._supervisor_agent)
            graph.add_node(LLM_AGENT, self._llm_agent)
            graph.add_node(EMBEDDING_AGENT, self._embedding_agent)
            graph.add_node(SPARSE_AGENT, self._sparse_agent)
            graph.add_node(DATABASE_AGENT, self._database_agent)

            # Edges

            graph.add_edge(START, SUPERVISOR_AGENT)

            graph.add_edge(SUPERVISOR_AGENT, LLM_AGENT)
            graph.add_edge(SUPERVISOR_AGENT, EMBEDDING_AGENT)
            graph.add_edge(SUPERVISOR_AGENT, SPARSE_AGENT)

            graph.add_edge(LLM_AGENT, DATABASE_AGENT)
            graph.add_edge(EMBEDDING_AGENT, DATABASE_AGENT)
            graph.add_edge(SPARSE_AGENT, DATABASE_AGENT)

            graph.add_edge(DATABASE_AGENT, END)            

            workflow = graph.compile()
            mermaid = workflow.get_graph().draw_mermaid()
            print(mermaid)
            logger.info({"message": "Graph built successfully"})

            return workflow

        except Exception as e:
            logger.error({"message": "Failed to build graph", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            pass

    async def _supervisor_agent(self, state: DIGState):
        pass

    async def _llm_agent(self, state: DIGState):
        pass

    async def _embedding_agent(self, state: DIGState):
        pass

    async def _sparse_agent(self, state: DIGState):
        pass

    async def _database_agent(self, state: DIGState):
        pass
