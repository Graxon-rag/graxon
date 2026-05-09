from ...schemas.chunk_schema import Chunk, ChunkEmbedding, ChunkSparseEmbedding, ChunkTags, TagResponse, ChunkTagResult, N4jChunkEdge
from app.core.lexical_engine.index import LexicalEngine, LEChunk, LexicalResult
from ..provider import WorkflowEmbedder, WorkflowSparseEmbedder, WorkflowLLM
from fastembed.sparse.sparse_embedding_base import SparseEmbedding
from app.core.schemas.document_schema import DocumentGetSchema
from .processor.processor_factory import ProcessorFactory
from app.core.helpers.minio_helper import MinioHelper
from ..schemas.provider_schema import ProviderSchema
from langgraph.graph import StateGraph, START, END
from typing import Dict, List, Optional, Annotated
from app.core.qdrant.inject import QdrantInjector
from .prompts.tag_prompt import Tagging_Prompt
from app.constants.minio import MinioConstant
from langchain_core.documents import Document
from app.constants.neo4j import GNeo4jEdges
from app.core.neo4j.chunk import GN4jChunk
from app.core.libs.id import IDLibs
from app.utils.logger import logger
from typing import TypedDict, Tuple
from langgraph.types import Send
import traceback
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
VECTOR_DATABASE_AGENT = "vector_database_agent"
GRAPH_DATABASE_AGENT = "graph_database_agent"


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
    tags: Optional[List[ChunkTags] | None]
    chunk_tag_results: Optional[List[ChunkTagResult] | None]
    lexical_engine_data: Optional[LexicalResult | None]
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
        self.n4j_chunk_db = GN4jChunk(org_id=org_id, project_id=project_id)

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
            graph.add_node(VECTOR_DATABASE_AGENT, self._vector_database_agent)
            graph.add_node(GRAPH_DATABASE_AGENT, self._graph_database_agent)

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
            graph.add_edge(LLM_AGENT, VECTOR_DATABASE_AGENT)
            graph.add_edge(EMBEDDING_AGENT, VECTOR_DATABASE_AGENT)
            graph.add_edge(SPARSE_AGENT, VECTOR_DATABASE_AGENT)
            graph.add_edge(LEXICAL_ENGINE_AGENT, VECTOR_DATABASE_AGENT)

            graph.add_edge(VECTOR_DATABASE_AGENT, GRAPH_DATABASE_AGENT)

            graph.add_edge(GRAPH_DATABASE_AGENT, END)

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

            # tags: List[ChunkTags] = state["tags"] or []
            providers = state["providers"]
            llm_provider = providers.llm.provider
            api_key = providers.llm.api_key
            model = providers.llm.model

            llm = WorkflowLLM.llm(provider=llm_provider, api_key=api_key, model=model)
            structured_llm = llm.with_structured_output(TagResponse)

            global_tags: List[str] = []
            chunk_tag_results: List[ChunkTagResult] = []   # in-memory store

            for chunk in chunks:
                try:
                    logger.info({"message": "LLM chunk", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                    existing_tags_str = ", ".join(global_tags) if global_tags else "None yet — this is the first chunk."
                    formatted_prompt = Tagging_Prompt.format(
                        existing_tags=existing_tags_str,
                        chunk_text=chunk.text,
                    )
                    tag_response: TagResponse = await structured_llm.ainvoke(formatted_prompt)

                    # hallucination guard
                    tag_response.validate_similar_tags_against_pool(global_tags)

                    # grow global pool
                    for new_tag in tag_response.new_tags:
                        if new_tag not in global_tags:
                            global_tags.append(new_tag)

                    # store in memory — nothing else
                    chunk_tag_results.append(ChunkTagResult(
                        chunk_id=chunk.chunk_id,
                        chunk_number=chunk.chunk_number,
                        tag_response=tag_response,
                    ))

                except Exception as e:
                    logger.error({"message": "Failed to run LLM agent", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})

            # Upload LLM results
            chunk_result_json = [chunk_result.model_dump_json() for chunk_result in chunk_tag_results]
            await self.minio_helper.upload_json(json_file_name=MinioConstant.LLM_OUTPUT_FILE, json_data={"data": chunk_result_json}, document_name_id=self.document_readable_id)

            return {"chunk_tag_results": chunk_tag_results}
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
            loop = asyncio.get_running_loop()
            for chunk in chunks:
                try:
                    logger.info({"message": "Sparse embedding chunk", "chunk_number": chunk.chunk_number, "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                    em_vector: SparseEmbedding = await loop.run_in_executor(None, sparse_embedder.embed, chunk.text)
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
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, lexical_engine.run_lexical_engine, le_chunks)

            await MinioHelper(org_id=self.org_id, project_id=self.project_id).upload_json(json_file_name=MinioConstant.LEXICAL_ENGINE_OUTPUT_FILE, json_data=result.model_dump(), document_name_id=self.document_readable_id)

            lexical_engine_data = result
            return {"lexical_engine_data": lexical_engine_data}
        except Exception as e:
            logger.error({"message": "Failed to run lexical engine agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            raise e

    async def _vector_database_agent(self, state: DIGState):
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

    async def _graph_database_agent(self, state: DIGState):
        try:
            chunks = state["chunks"]
            if chunks is None:
                logger.error({"message": "Chunks is None", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise ValueError("Chunks embeddings is None")
            logger.info({"message": "Creating graph database", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})

            await self.n4j_chunk_db.create_multiple(self.document_id, self.document_readable_id, chunks)

            lexical_engine_data = state["lexical_engine_data"]
            if lexical_engine_data is not None:
                logger.info({"message": "Creating graph database edges", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                await self.n4j_chunk_db.create_edges_by_lexical_engine_data(self.document_id, self.document_readable_id, lexical_engine_data)

            chunk_tag_results = state["chunk_tag_results"]
            if chunk_tag_results is not None:
                logger.info({"message": "Creating graph database edges", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                tags = await self._llm_agent_process(chunk_results=chunk_tag_results, chunks=chunks)

                # Upload LLM tags
                tags_json = [tag.model_dump_json() for tag in tags]
                await self.minio_helper.upload_json(json_file_name=MinioConstant.LLM_TAG_RESPONSE, json_data={"data": tags_json}, document_name_id=self.document_readable_id)

        except Exception as e:
            logger.error({"message": "Failed to run graph database agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            raise e

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

    def _build_tag_map(self, chunk_results: List[ChunkTagResult]) -> Dict[str, List[Tuple[str, float]]]:
        """
        Returns:
        {
            "tag_name": [(chunk_id, confidence), (chunk_id, confidence), ...]
        }
        new_tags always get confidence 1.0
        similar_tags use LLM confidence score
        """
        tag_map: Dict[str, List[Tuple[str, float]]] = {}

        for result in chunk_results:
            # new_tags — confidence always 1.0
            for tag in result.tag_response.new_tags:
                tag_map.setdefault(tag, [])
                tag_map[tag].append((result.chunk_id, 1.0))

            # similar_tags — LLM confidence
            for similar in result.tag_response.similar_tags:
                tag_map.setdefault(similar.tag, [])
                tag_map[similar.tag].append((result.chunk_id, similar.confidence))

        return tag_map

    # TEXT SEARCH
    def _find_referenced_chunks(self, reference_hint: str, chunks: list[Chunk], current_chunk_number: int) -> List[int]:
        matched = []
        hint_lower = reference_hint.strip().lower()

        vague_signals = ["earlier", "above", "previous", "before", "prior", "as defined", "as mentioned"]
        is_vague = any(signal in hint_lower for signal in vague_signals)

        if is_vague:
            prev = current_chunk_number - 1
            if prev >= 0:
                matched.append(prev)
            return matched

        for chunk in chunks:
            if chunk.chunk_number == current_chunk_number:
                continue
            if hint_lower in chunk.text.lower():
                matched.append(chunk.chunk_number)

        return matched

    # POST PROCESSING
    async def _llm_agent_process(self, chunk_results: List[ChunkTagResult], chunks: list[Chunk]) -> List[ChunkTags]:
        """
        - Text search for all reference_hints
        - Build ChunkTags
        - Create all Neo4j edges
        """
        all_chunk_tags: List[ChunkTags] = []

        # BUILD TAG MAP
        tag_map = self._build_tag_map(chunk_results)

        n4j_tag_edges: list[N4jChunkEdge] = []
        n4j_nex_prev_edges: list[N4jChunkEdge] = []
        n4j_reference_edges: list[N4jChunkEdge] = []

        # HAS_TAG EDGES: chunk → chunk (bidirectional, avg confidence)
        for tag, chunk_confidences in tag_map.items():
            # need at least 2 chunks sharing a tag to create an edge
            if len(chunk_confidences) < 2:
                continue

            for i in range(len(chunk_confidences)):
                for j in range(len(chunk_confidences)):
                    if i == j:
                        continue

                    chunk_id_a, conf_a = chunk_confidences[i]
                    chunk_id_b, conf_b = chunk_confidences[j]
                    avg_weight = round((conf_a + conf_b) / 2, 2)

                    n4j_tag_edges.append(N4jChunkEdge(
                        from_chunk_id=chunk_id_a,
                        to_chunk_id=chunk_id_b,
                        edge_name=GNeo4jEdges.HAS_TAG,
                        label=tag,
                        weight=avg_weight,
                    ))

        # PER CHUNK: NEXT/PREV + REFERENCES
        for result in chunk_results:
            chunk_id = result.chunk_id
            chunk_number = result.chunk_number
            tag_response = result.tag_response

            # RESOLVE REFERENCES
            reference_chunk_numbers = []
            if tag_response.has_backward_reference and tag_response.reference_hint:
                reference_chunk_numbers = self._find_referenced_chunks(
                    reference_hint=tag_response.reference_hint,
                    chunks=chunks,
                    current_chunk_number=chunk_number,
                )

            # BUILD ChunkTags
            chunk_tags = ChunkTags(
                chunk_id=chunk_id,
                chunk_number=chunk_number,
                new_tags=tag_response.new_tags,
                similar_tags=tag_response.similar_tags,
                reference_chunk_numbers=reference_chunk_numbers,
            )
            all_chunk_tags.append(chunk_tags)

            # NEXT / PREV EDGES
            if chunk_number > 0:
                prev_chunk = chunks[chunk_number - 1]

                n4j_nex_prev_edges.append(N4jChunkEdge(
                    from_chunk_id=chunk_id,
                    to_chunk_id=prev_chunk.chunk_id,
                    edge_name=GNeo4jEdges.PREV,
                    label="sequential",
                    weight=1.0,
                ))
                n4j_nex_prev_edges.append(N4jChunkEdge(
                    from_chunk_id=prev_chunk.chunk_id,
                    to_chunk_id=chunk_id,
                    edge_name=GNeo4jEdges.NEXT,
                    label="sequential",
                    weight=1.0,
                ))

            # REFERENCES EDGES
            for ref_chunk_number in reference_chunk_numbers:
                ref_chunk = chunks[ref_chunk_number]
                if len(reference_chunk_numbers) == 1:
                    ref_weight = 1.0 if tag_response.reference_hint != "previous" else 0.6
                else:
                    ref_weight = 0.7

                n4j_reference_edges.append(N4jChunkEdge(
                    from_chunk_id=chunk_id,
                    to_chunk_id=ref_chunk.chunk_id,
                    edge_name=GNeo4jEdges.REFERENCES,
                    label=tag_response.reference_hint or "_",
                    weight=ref_weight,
                ))

        n4j_tag_edges_json = [edge.model_dump_json() for edge in n4j_tag_edges]
        n4j_nex_prev_edges_json = [edge.model_dump_json() for edge in n4j_nex_prev_edges]
        n4j_reference_edges_json = [edge.model_dump_json() for edge in n4j_reference_edges]

        # UPLOAD TO MINIO
        await self.minio_helper.upload_json(json_file_name=MinioConstant.N4J_EDGES_TAG_OUTPUT, json_data={"data": n4j_tag_edges_json}, document_name_id=self.document_readable_id)
        await self.minio_helper.upload_json(json_file_name=MinioConstant.N4J_EDGES_NEXT_PREV_OUTPUT, json_data={"data": n4j_nex_prev_edges_json}, document_name_id=self.document_readable_id)
        await self.minio_helper.upload_json(json_file_name=MinioConstant.N4J_EDGES_REFERENCE_OUTPUT, json_data={"data": n4j_reference_edges_json}, document_name_id=self.document_readable_id)

        # Merge TO NEO4J
        await self.n4j_chunk_db.create_edges(self.document_id, n4j_tag_edges)
        await self.n4j_chunk_db.create_edges(self.document_id, n4j_nex_prev_edges)
        await self.n4j_chunk_db.create_edges(self.document_id, n4j_reference_edges)

        return all_chunk_tags
