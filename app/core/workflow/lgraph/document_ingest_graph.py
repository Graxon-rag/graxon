from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from app.core.schemas.document_schema import DocumentGetSchema
from app.core.helpers.minio_helper import MinioHelper
from ..schemas.provider_schema import ProviderSchema
from .processor.processor_factory import ProcessorFactory
from ..schemas.chunk_schema import Chunk
from app.utils.logger import logger
from ..provider import WorkflowEmbedder, WorkflowSparseEmbedder, WorkflowLLM
from typing import Dict, List, Optional
from langchain_core.documents import Document
import uuid
import os


SUPERVISOR_AGENT = "supervisor_agent"
CHUNKS_PARSER_AGENT = "CHUNKS_PARSER_AGENT"
LLM_AGENT = "llm_agent"
EMBEDDING_AGENT = "embedding_agent"
SPARSE_AGENT = "sparse_agent"
CHUNK_PROCESSOR_AGENT = "chunk_processor_agent"
DATABASE_AGENT = "database_agent"


class DIGState(TypedDict):
    org_id: str
    project_id: uuid.UUID
    document_id: uuid.UUID
    request_id: str
    document: DocumentGetSchema
    providers: ProviderSchema

    temp_path: str | None
    file_path: str | None

    chunk_size: int
    chunk_overlap: int

    chunks: Optional[List[Chunk] | None]


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
            graph.add_node(CHUNKS_PARSER_AGENT, self._chunks_parser_agent)
            graph.add_node(LLM_AGENT, self._llm_agent)
            graph.add_node(EMBEDDING_AGENT, self._embedding_agent)
            graph.add_node(SPARSE_AGENT, self._sparse_agent)
            graph.add_node(CHUNK_PROCESSOR_AGENT, self._chunks_processor_agent)
            graph.add_node(DATABASE_AGENT, self._database_agent)

            # Edges

            graph.add_edge(START, SUPERVISOR_AGENT)
            graph.add_edge(SUPERVISOR_AGENT, CHUNKS_PARSER_AGENT)

            graph.add_edge(CHUNKS_PARSER_AGENT, LLM_AGENT)
            graph.add_edge(CHUNKS_PARSER_AGENT, EMBEDDING_AGENT)
            graph.add_edge(CHUNKS_PARSER_AGENT, SPARSE_AGENT)

            graph.add_edge(LLM_AGENT, CHUNK_PROCESSOR_AGENT)
            graph.add_edge(EMBEDDING_AGENT, CHUNK_PROCESSOR_AGENT)
            graph.add_edge(SPARSE_AGENT, CHUNK_PROCESSOR_AGENT)

            graph.add_edge(CHUNK_PROCESSOR_AGENT, DATABASE_AGENT)

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
        try:
            document = state["document"]
            bucket = document.bucket
            key = document.key
            download_path = self._get_temp_path()

            # Update state so we can delete the temp folder
            state["temp_path"] = download_path

            logger.info({"message": "Downloading document", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "path": download_path})

            file_path = await MinioHelper(self.org_id, self.project_id).download_file(bucket=bucket, key=key, download_path=download_path, file_name=document.name)

            logger.info({"message": "Document downloaded successfully", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "path": download_path})

            state["file_path"] = file_path
            return state

        except Exception as e:
            logger.error({"message": "Failed to run supervisor agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            pass

    async def _chunks_parser_agent(self, state: DIGState):
        try:
            temp_path = state["temp_path"]
            if temp_path is None:
                logger.error({"message": "Temp path is None", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise
            file_path = state["file_path"]
            if file_path is None:
                logger.error({"message": "File path is None", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise

            processor = ProcessorFactory().get_processor(file_path=file_path)
            if processor is None:
                logger.error({"message": "Processor is None", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise

            processed_data: Dict[str, List[Document]] = processor.process(file_path=file_path, chunk_size=state["chunk_size"], chunk_overlap=state["chunk_overlap"])
            raw_chunks = processed_data["chunks"]

            chunks: List[Chunk] = []
            for idx, chunk in enumerate(raw_chunks):
                text = chunk.page_content or ""
                if text == "":
                    continue
                c = Chunk(
                    chunk_number=idx,
                    text=text,
                    title=chunk.metadata.get("title"),
                    source=chunk.metadata.get("source"),
                    page_number=chunk.metadata.get("'page'"),
                )
                chunks.append(c)

            state["chunks"] = chunks

            return state

        except Exception as e:
            logger.error({"message": "Failed to run chunks parser agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            pass

    async def _llm_agent(self, state: DIGState):
        try:
            chunks = state["chunks"]
            if chunks is None:
                logger.error({"message": "Chunks is None", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise

            providers = state["providers"]
            llm_provider = providers.llm.provider
            api_key = providers.llm.api_key
            model = providers.llm.model

            kwargs = {}
            llm = WorkflowLLM.llm(provider=llm_provider, api_key=api_key, model=model, kwargs=kwargs)

            for chunk in chunks:
                try:

                    logger.info({"message": "LLM chunk", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                    pass
                except Exception as e:
                    logger.error({"message": "Failed to run LLM agent", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})

        except Exception as e:
            logger.error({"message": "Failed to run LLM agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            pass

    async def _embedding_agent(self, state: DIGState):
        try:
            chunks = state["chunks"]
            if chunks is None:
                logger.error({"message": "Chunks is None", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise

            providers = state["providers"]
            embedder_provider = providers.embedding.provider
            api_key = providers.embedding.api_key
            model = providers.embedding.model

            kwargs = {}
            embedder = WorkflowEmbedder.embedder(provider=embedder_provider, api_key=api_key, model=model, kwargs=kwargs)
            for chunk in chunks:
                try:
                    # em_vector: list[float] = await embedder.aembed(chunk.text)
                    logger.info({"message": "Embedding chunk", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                    pass
                except Exception as e:
                    logger.error({"message": "Failed to run embedding agent", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
                    pass
        except Exception as e:
            logger.error({"message": "Failed to run embedding agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            pass

    async def _sparse_agent(self, state: DIGState):
        try:
            chunks = state["chunks"]
            if chunks is None:
                logger.error({"message": "Chunks is None", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise
            providers = state["providers"]
            sparse_provider = providers.sparse_model.provider
            sparse_model = providers.sparse_model.model

            sparse_embedder = WorkflowSparseEmbedder.sparse_embedder(model=sparse_model, provider=sparse_provider)
            for chunk in chunks:
                try:
                    # em_vector: list[float] = await embedder.aembed(chunk.text)
                    logger.info({"message": "Sparse embedding chunk", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                    pass
                except Exception as e:
                    logger.error({"message": "Failed to run sparse agent", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
                    pass

        except Exception as e:
            logger.error({"message": "Failed to run sparse agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            pass

    async def _database_agent(self, state: DIGState):
        pass

    async def _chunks_processor_agent(self, state: DIGState):
        pass

    def _get_temp_path(self) -> str:
        base_tmp_path = "/tmp/graxon"

        # Create unique folder using UUID
        run_id = str(uuid.uuid4())
        run_path = os.path.join(base_tmp_path, run_id)

        # Ensure directory exists
        os.makedirs(run_path, exist_ok=True)
        return run_path
