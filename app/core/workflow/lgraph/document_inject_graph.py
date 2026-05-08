from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from app.core.schemas.document_schema import DocumentGetSchema
from app.core.helpers.minio_helper import MinioHelper
from ..schemas.provider_schema import ProviderSchema
from .processor.processor_factory import ProcessorFactory
from ...schemas.chunk_schema import Chunk, ChunkEmbedding, ChunkSparseEmbedding
from app.core.lexical_engine.index import LexicalEngine, LEChunk
from app.constants.minio import MinioConstant
from app.core.libs.id import IDLibs
from app.utils.logger import logger
from ..provider import WorkflowEmbedder, WorkflowSparseEmbedder, WorkflowLLM
from fastembed.sparse.sparse_embedding_base import SparseEmbedding
from app.core.qdrant.inject import QdrantInjector
from typing import Dict, List, Optional, Annotated
from langgraph.types import Send
import traceback
from langchain_core.documents import Document
import operator
import asyncio
import uuid
import os


SUPERVISOR_AGENT = "supervisor_agent"
CHUNKS_PARSER_AGENT = "chunks_parser_agent"
LLM_AGENT = "llm_agent"
EMBEDDING_AGENT = "embedding_agent"
SPARSE_AGENT = "sparse_agent"
LEXICAL_ENGINE_AGENT = "lexical_engine_agent"
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
    chunks_embeddings: Annotated[List[ChunkEmbedding], operator.add]
    chunks_sparse_embeddings: Annotated[List[ChunkSparseEmbedding], operator.add]


class DocumentInjectGraph:
    def __init__(self, org_id: str, project_id: uuid.UUID, document_id: uuid.UUID, document_readable_id: str):
        self.org_id = org_id
        self.project_id = project_id
        self.document_id = document_id
        self.document_readable_id = document_readable_id
        self.injector = QdrantInjector(org_id=org_id, project_id=project_id)
        self.minio_helper = MinioHelper(org_id=org_id, project_id=project_id)

    def build_graph(self):
        try:
            graph = StateGraph(DIGState)

            # Nodes
            graph.add_node(SUPERVISOR_AGENT, self._supervisor_agent)
            graph.add_node(CHUNKS_PARSER_AGENT, self._chunks_parser_agent)
            graph.add_node(LLM_AGENT, self._llm_agent)
            graph.add_node(EMBEDDING_AGENT, self._embedding_agent)
            graph.add_node(SPARSE_AGENT, self._sparse_agent)
            graph.add_node(LEXICAL_ENGINE_AGENT, self._lexical_engine_agent)
            graph.add_node(CHUNK_PROCESSOR_AGENT, self._chunks_processor_agent)
            graph.add_node(DATABASE_AGENT, self._database_agent)

            # Edges

            graph.add_edge(START, SUPERVISOR_AGENT)
            graph.add_edge(SUPERVISOR_AGENT, CHUNKS_PARSER_AGENT)

            # Fan-out: chunks_parser dispatches all 4 agents simultaneously
            graph.add_conditional_edges(
                CHUNKS_PARSER_AGENT,
                self._fan_out,
                [LLM_AGENT, EMBEDDING_AGENT, SPARSE_AGENT, LEXICAL_ENGINE_AGENT],
            )

            # Fan-in: all 4 converge on chunk_processor
            graph.add_edge(LLM_AGENT, CHUNK_PROCESSOR_AGENT)
            graph.add_edge(EMBEDDING_AGENT, CHUNK_PROCESSOR_AGENT)
            graph.add_edge(SPARSE_AGENT, CHUNK_PROCESSOR_AGENT)
            graph.add_edge(LEXICAL_ENGINE_AGENT, CHUNK_PROCESSOR_AGENT)            

            workflow = graph.compile()
            mermaid = workflow.get_graph().draw_mermaid()
            print(mermaid)
            logger.info({"message": "Graph built successfully"})

            return workflow

        except Exception as e:
            logger.error({"message": "Failed to build graph", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            pass

    def _fan_out(self, state: DIGState) -> list[Send]:
        # Each Send dispatches a node with a copy of the current state.
        # LangGraph runs all of them concurrently.
        return [
            Send(LLM_AGENT, state),
            Send(EMBEDDING_AGENT, state),
            Send(SPARSE_AGENT, state),
            Send(LEXICAL_ENGINE_AGENT, state),
        ]

    async def _supervisor_agent(self, state: DIGState):
        try:
            document = state["document"]
            bucket = document.bucket
            key = document.key
            download_path = self._get_temp_path()

            logger.info({"message": "Downloading document", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "path": download_path})

            file_path = await MinioHelper(self.org_id, self.project_id).download_file(bucket=bucket, key=key, download_path=download_path, file_name=document.name)

            logger.info({"message": "Document downloaded successfully", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "path": download_path})

            return {"file_path": file_path, "temp_path": download_path}

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
                    chunk_id=IDLibs.generate_chunk_id(document_id=self.document_readable_id, chunk_number=idx),
                    chunk_number=idx,
                    text=text,
                    title=chunk.metadata.get("title"),
                    source=chunk.metadata.get("source"),
                    page_number=chunk.metadata.get("page"),
                )
                chunks.append(c)

            return {"chunks": chunks}

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

            llm = WorkflowLLM.llm(provider=llm_provider, api_key=api_key, model=model)

            for chunk in chunks:
                try:

                    logger.info({"message": "LLM chunk", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                    pass
                except Exception as e:
                    logger.error({"message": "Failed to run LLM agent", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})

        except Exception as e:
            logger.error({"message": "Failed to run LLM agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e), "traceback": traceback.format_exc()})
            raise e

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
            dimension = providers.embedding.dimension

            embedder = WorkflowEmbedder.embedder(provider=embedder_provider, api_key=api_key, model=model, dimension=dimension)

            chs_embeddings: List[ChunkEmbedding] = []
            for chunk in chunks:
                try:
                    logger.info({"message": "Embedding chunk", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                    em_vector: list[float] = await embedder.aembed(chunk.text)
                    chs_embeddings.append(ChunkEmbedding(chunk_id=chunk.chunk_id, chunk_number=chunk.chunk_number, embedding=em_vector))
                except Exception as e:
                    logger.error({"message": "Failed to run embedding agent", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})

            # save embeddings
            data_for_minio = {"data": [chunk.model_dump_json() for chunk in chs_embeddings]}
            minio_file_name = MinioConstant.EMBEDDING_OUTPUT_FILE
            await MinioHelper(org_id=self.org_id, project_id=self.project_id).upload_json(json_file_name=minio_file_name, json_data=data_for_minio, document_name_id=self.document_readable_id)

            return {"chunks_embeddings": chs_embeddings}

        except Exception as e:
            logger.error({"message": "Failed to run embedding agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e), "traceback": traceback.format_exc()})
            raise e

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
            chs_sparse_embeddings: List[ChunkSparseEmbedding] = []
            for chunk in chunks:
                try:
                    logger.info({"message": "Sparse embedding chunk", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                    em_vector: SparseEmbedding = sparse_embedder.embed(chunk.text)
                    chs_sparse_embeddings.append(ChunkSparseEmbedding(chunk_id=chunk.chunk_id, chunk_number=chunk.chunk_number, embedding=em_vector))
                except Exception as e:
                    logger.error({"message": "Failed to run sparse agent", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})

            # Upload sparse embeddings
            data_for_minio = {"data": [chunk.model_dump_json() for chunk in chs_sparse_embeddings]}
            minio_file_name = MinioConstant.SPARSE_EMBEDDING_OUTPUT_FILE

            await self.minio_helper.upload_json(json_file_name=minio_file_name, json_data=data_for_minio, document_name_id=self.document_readable_id)

            return {"chunks_sparse_embeddings": chs_sparse_embeddings}
        except Exception as e:
            logger.error({"message": "Failed to run sparse agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e), "traceback": traceback.format_exc()})
            raise e

    async def _lexical_engine_agent(self, state: DIGState):
        try:
            chunks = state["chunks"]
            if chunks is None:
                logger.error({"message": "Chunks is None", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise ValueError("Chunks embeddings is None")
            lexical_engine = LexicalEngine()

            le_chunks: List[LEChunk] = []
            for chunk in chunks:
                le_chunks.append(LEChunk(chunk_id=chunk.chunk_id, chunk_number=chunk.chunk_number, text=chunk.text))

            result = lexical_engine.run_lexical_engine(le_chunks)
            await MinioHelper(org_id=self.org_id, project_id=self.project_id).upload_json(json_file_name=MinioConstant.LEXICAL_ENGINE_OUTPUT_FILE, json_data=result.model_dump(), document_name_id=self.document_readable_id)

        except Exception as e:
            logger.error({"message": "Failed to run lexical engine agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            raise e

    async def _chunks_processor_agent(self, state: DIGState):
        try:
            chunks = state["chunks"]
            if chunks is None:
                logger.error({"message": "Chunks is None", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise ValueError("Chunks embeddings is None")
            chunks_embeddings = state["chunks_embeddings"]
            chunks_sparse_embeddings = state["chunks_sparse_embeddings"]

            if chunks_embeddings is None:
                logger.error({"message": "Chunks embeddings is None", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise ValueError("Chunks sparse embeddings is None")
            if chunks_sparse_embeddings is None:
                logger.error({"message": "Chunks sparse embeddings is None", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise ValueError("Chunks sparse embeddings is None")

            providers = state["providers"]
            embedder_provider = providers.embedding.provider.value  # Use .value because it's a enum
            dimension = providers.embedding.dimension
            model_key = self._get_model_key(embedder_provider, dimension)

            await self.injector.inject(model_key=model_key, document_id=self.document_id, chunks=chunks, chunk_embeddings=chunks_embeddings, chunk_sparse_embeddings=chunks_sparse_embeddings)

        except Exception as e:
            logger.error({"message": "Failed to run chunks processor agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            raise e

    async def _database_agent(self, state: DIGState):
        pass

    def _get_temp_path(self) -> str:
        base_tmp_path = "/tmp/graxon"

        # Create unique folder using UUID
        run_id = str(uuid.uuid4())
        run_path = os.path.join(base_tmp_path, run_id)

        # Ensure directory exists
        os.makedirs(run_path, exist_ok=True)
        return run_path

    def _get_model_key(self, provider: str, dimension: int) -> str:
        return f"{provider}_{dimension}"
