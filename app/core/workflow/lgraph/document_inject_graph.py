from ...schemas.chunk_schema import Chunk, ChunkEmbedding, ChunkSparseEmbedding, ChunkTags, TagResponse, ChunkTagResult, N4jChunkEdge, ChunkDenseVectorScore
from app.core.lexical_engine.index import LexicalEngine, LEChunk, LexicalResult
from ..provider import WorkflowEmbedder, WorkflowSparseEmbedder, WorkflowLLM
from ...schemas.project_config_schema import ProjectConfigDetailGetSchema
from app.core.redis.sparse_embedding import GRedisSparseEmbeddingClient
from fastembed.sparse.sparse_embedding_base import SparseEmbedding
from app.core.schemas.neo4j_schema import LexicalSemanticResult
from app.core.redis.embeddings import GRedisEmbeddingsClient
from app.core.qdrant.similarity import QdrantSimilarity
from app.constants.neo4j import GNeo4jEdges, GN4jNodes
from app.core.helpers.minio_helper import MinioHelper
from app.core.redis.dig_redis import DIGRedisClient
from langgraph.graph import StateGraph, START, END
from typing import Dict, List, Optional, Annotated
from app.core.qdrant.inject import QdrantInjector
from app.core.redis.tags import GRedisTagsClient
from app.constants.redis import GRedisConstant
from .prompts.tag_prompt import Tagging_Prompt
from ...schemas import processor_schema as ps
from app.constants.minio import MinioConstant
from app.core.neo4j.interfaces import common
from app.core.neo4j.chunk import GN4jChunk
from app.utils.logger import logger
from collections import defaultdict
from typing import TypedDict, Tuple
from langgraph.types import Send
from app.config.env import Env
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
SIMILARITY_SYNC_AGENT = "similarity_sync_agent"


class DIGState(TypedDict):
    org_id: str
    project_id: uuid.UUID
    document_id: uuid.UUID
    request_id: str
    ep_model_key: str
    project_config: ProjectConfigDetailGetSchema

    chunks: List[Chunk]
    tags: Optional[List[ChunkTags] | None]
    chunk_tag_results: Optional[List[ChunkTagResult] | None]
    lexical_engine_data: Optional[LexicalResult | None]
    chunks_embeddings: Annotated[List[ChunkEmbedding], operator.add]
    chunks_sparse_embeddings: Annotated[List[ChunkSparseEmbedding], operator.add]


class DocumentInjectGraph:
    def __init__(self, cp: ps.CommonParams):
        self.org_id = cp.org_id
        self.project_id = cp.project_id
        self.document_id = cp.doc_id
        self.document_readable_id = cp.doc_readable_id
        self.n4j_chunk_db = GN4jChunk(org_id=self.org_id, project_id=self.project_id)
        self.injector = QdrantInjector(org_id=self.org_id, project_id=self.project_id)
        self.minio_helper = MinioHelper(org_id=self.org_id, project_id=self.project_id)
        self._tag_redis = GRedisTagsClient(org_id=self.org_id, project_id=self.project_id)
        self.qdrant_similarity = QdrantSimilarity(org_id=self.org_id, project_id=self.project_id)
        self._embedding_redis = GRedisEmbeddingsClient(org_id=self.org_id, project_id=self.project_id)
        self._sparse_embedding_redis = GRedisSparseEmbeddingClient(org_id=self.org_id, project_id=self.project_id)
        self._dig_redis = DIGRedisClient(org_id=self.org_id, project_id=self.project_id, document_id=self.document_id)

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
            graph.add_node(SIMILARITY_SYNC_AGENT, self._similarity_sync_agent)

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

            graph.add_edge(GRAPH_DATABASE_AGENT, SIMILARITY_SYNC_AGENT)

            graph.add_edge(SIMILARITY_SYNC_AGENT, END)

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
            logger.info({"message": "Running supervisor agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})

        except Exception as e:
            logger.error({"message": "Failed to run supervisor agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            pass

    async def _chunks_parser_agent(self, state: DIGState):
        try:
            logger.info({"message": "Running chunks parser agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
        except Exception as e:
            logger.error({"message": "Failed to run chunks parser agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            raise e

    async def _llm_agent(self, state: DIGState):
        try:
            project_config = state["project_config"]
            is_tag_extraction_enabled = project_config.llm_tag_extraction_enable
            if not is_tag_extraction_enabled:
                logger.warning({"message": "LLM Tag Extraction is disabled", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                return

            llm_model = project_config.llm_model
            llm_model_credential = project_config.llm_model_credential
            if llm_model is None or llm_model_credential is None:
                logger.warning({"message": "LLM Model is not configured", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                return

            chunks = state["chunks"]
            llm_provider = llm_model.provider
            model = llm_model.model_id
            api_key = llm_model_credential.api_key

            llm = WorkflowLLM.llm(provider=llm_provider, api_key=api_key, model=model)
            structured_llm = llm.with_structured_output(TagResponse)

            # Rebuild global_tags pool from already-processed chunks
            # So the LLM still gets correct context for the remaining chunks            
            global_tags: List[str] = []
            chunk_tag_results: List[ChunkTagResult] = []

            BATCH_SIZE = Env.LLM_TAG_EXTRACTION_BATCH_SIZE  # 5 to 10 chunks per batch to prevent rate limit spikes

            async def process_single_chunk(chunk: Chunk, current_global_tags: List[str]) -> ChunkTagResult:
                """Helper to process and safely handle errors for a single chunk."""
                try:
                    existing_tags_str = ", ".join(current_global_tags) if current_global_tags else "None yet — this is the first chunk."
                    formatted_prompt = Tagging_Prompt.format(
                        existing_tags=existing_tags_str,
                        chunk_text=chunk.text,
                    )

                    tag_response: Optional[TagResponse] = await structured_llm.ainvoke(formatted_prompt)

                    # Guard against None / invalid parsing
                    if tag_response is None:
                        logger.warning({
                            "message": "LLM returned None for chunk, falling back to empty TagResponse",
                            "chunk_number": chunk.chunk_number
                        })
                        tag_response = TagResponse(
                            new_tags=[],
                            similar_tags=[],
                            has_backward_reference=False,
                            reference_hint=None
                        )

                    # Hallucination guard
                    tag_response.validate_similar_tags_against_pool(current_global_tags)

                    return ChunkTagResult(
                        chunk_id=chunk.chunk_id,
                        chunk_number=chunk.chunk_number,
                        tag_response=tag_response,
                    )

                except Exception as e:
                    logger.warning({
                        "message": "LLM agent failed on chunk, using fallback empty TagResponse",
                        "chunk_number": chunk.chunk_number,
                        "error": str(e)
                    })
                    fallback_resp = TagResponse(
                        new_tags=[],
                        similar_tags=[],
                        has_backward_reference=False,
                        reference_hint=None
                    )
                    return ChunkTagResult(
                        chunk_id=chunk.chunk_id,
                        chunk_number=chunk.chunk_number,
                        tag_response=fallback_resp,
                    )

            #  Run batches in sequence while running chunks inside each batch in parallel
            for i in range(0, len(chunks), BATCH_SIZE):
                batch_chunks = chunks[i: i + BATCH_SIZE]
                chunk_numbers = [c.chunk_number for c in batch_chunks]

                logger.info({
                    "message": "Processing LLM chunk batch",
                    "chunk_numbers": chunk_numbers,
                    "document_id": self.document_id,
                    "org_id": self.org_id,
                    "project_id": self.project_id,
                    "batch_size": len(batch_chunks)
                })

                # Dispatch this batch concurrently with a snapshot of global_tags
                tasks = [process_single_chunk(c, global_tags) for c in batch_chunks]
                batch_results: List[ChunkTagResult] = await asyncio.gather(*tasks)

                # Update results and collect new tags for subsequent batches
                for res in batch_results:
                    chunk_tag_results.append(res)
                    for new_tag in res.tag_response.new_tags:
                        if new_tag not in global_tags:
                            global_tags.append(new_tag)

            # Sort final results by chunk_number
            chunk_tag_results.sort(key=lambda x: x.chunk_number)

            # Upload LLM results
            chunk_result_json = [chunk_result.model_dump_json() for chunk_result in chunk_tag_results]
            await self.minio_helper.upload_json(json_file_name=MinioConstant.LLM_OUTPUT_FILE, json_data={"data": chunk_result_json}, document_id=self.document_id)

            # await self._dig_redis.update_status(dig_node=GRedisConstant.LLM_NODE, status=GRedisConstant.DIG_NODE_STATUS_COMPLETED)
            return {"chunk_tag_results": chunk_tag_results}
        except Exception as e:
            logger.error({"message": "Failed to run LLM agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e), "traceback": traceback.format_exc()})
            raise e

    async def _embedding_agent(self, state: DIGState):
        try:
            chunks = state["chunks"]
            project_config = state["project_config"]
            embedding_model = project_config.embedding_model
            embedding_model_credential = project_config.embedding_model_credential
            if embedding_model is None or embedding_model_credential is None:
                logger.error({"message": "Embedding Model is not configured", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise ValueError("Embedding Model or Embedding Model Credential is not configured")

            embedder_provider = embedding_model.provider
            model = embedding_model.model_id
            dimension = embedding_model.dimension
            api_key = embedding_model_credential.api_key

            embedder = WorkflowEmbedder.embedder(provider=embedder_provider, api_key=api_key, model=model, dimension=dimension)

            chs_embeddings: List[ChunkEmbedding] = []
            BATCH_SIZE = Env.EMBEDDING_CHUNK_BATCH_SIZE

            # Process in slices of BATCH_SIZE chunks
            for i in range(0, len(chunks), BATCH_SIZE):
                batch_chunks = chunks[i: i + BATCH_SIZE]
                chunk_numbers = [c.chunk_number for c in batch_chunks]

                try:
                    logger.info({
                        "message": "Embedding chunk batch",
                        "chunk_numbers": chunk_numbers,
                        "document_id": self.document_id,
                        "org_id": self.org_id,
                        "project_id": self.project_id,
                        "batch_size": len(batch_chunks),
                    })

                    # Embed the batch of texts together
                    texts = [chunk.text for chunk in batch_chunks]
                    em_vectors: List[List[float]] = await embedder.aembed_batch(texts)

                    # # Concurrently save each embedding to Redis
                    # redis_tasks = [
                    #     self._embedding_redis.add_embedding_temporary(
                    #         document_id=self.document_id,
                    #         chunk_number=chunk.chunk_number,
                    #         embedding=vector,
                    #     )
                    #     for chunk, vector in zip(batch_chunks, em_vectors)
                    # ]
                    # await asyncio.gather(*redis_tasks)

                    # Append to final results list
                    for chunk, vector in zip(batch_chunks, em_vectors):
                        chs_embeddings.append(
                            ChunkEmbedding(
                                chunk_id=chunk.chunk_id,
                                chunk_number=chunk.chunk_number,
                                embedding=vector,
                            )
                        )

                except Exception as e:
                    logger.error({
                        "message": "Failed to run embedding agent for batch",
                        "chunk_numbers": chunk_numbers,
                        "document_id": self.document_id,
                        "org_id": self.org_id,
                        "project_id": self.project_id,
                        "error": str(e),
                    })
                    raise e

            # Sort final results by chunk_number before upload
            chs_embeddings.sort(key=lambda x: x.chunk_number)

            # save embeddings
            data_for_minio = {"data": [chunk.model_dump_json() for chunk in chs_embeddings]}
            minio_file_name = MinioConstant.EMBEDDING_OUTPUT_FILE
            await self.minio_helper.upload_json(json_file_name=minio_file_name, json_data=data_for_minio, document_id=self.document_id)
            # await self._dig_redis.update_status(dig_node=GRedisConstant.EMBEDDING_NODE, status=GRedisConstant.DIG_NODE_STATUS_COMPLETED)

            return {"chunks_embeddings": chs_embeddings}

        except Exception as e:
            logger.error({"message": "Failed to run embedding agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e), "traceback": traceback.format_exc()})
            raise e

    async def _sparse_agent(self, state: DIGState):
        try:
            chunks = state["chunks"]
            project_config = state["project_config"]

            if not project_config.sparse_embedding_enable:
                logger.warning({"message": "Sparse Embedding is not enabled", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                return {"chunks_sparse_embeddings": []}

            sparse_embedding_model = project_config.sparse_text_model
            sparse_embedding_model_credential = project_config.sparse_text_model_credential

            if sparse_embedding_model is None:
                logger.error({"message": "Sparse Embedding Model is not configured", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise ValueError("Sparse Embedding Model is not configured")

            if sparse_embedding_model.provider_type == "cloud" and sparse_embedding_model_credential is None:
                logger.error({"message": "Sparse Embedding Model Credential is not configured", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                raise ValueError("Sparse Embedding Model Credential is not configured")

            sparse_provider = sparse_embedding_model.provider
            sparse_model = sparse_embedding_model.model_id
            api_key: str | None = sparse_embedding_model_credential and sparse_embedding_model_credential.api_key

            sparse_embedder = WorkflowSparseEmbedder.sparse_embedder(model=sparse_model, provider=sparse_provider, provider_type=sparse_embedding_model.provider_type, api_key=api_key)
            chs_sparse_embeddings: List[ChunkSparseEmbedding] = []
            BATCH_SIZE = Env.SPARSE_CHUNK_BATCH_SIZE

            # Process chunks in batches of BATCH_SIZE
            for i in range(0, len(chunks), BATCH_SIZE):
                batch_chunks = chunks[i: i + BATCH_SIZE]
                chunk_numbers = [c.chunk_number for c in batch_chunks]

                try:
                    logger.info({
                        "message": "Sparse embedding chunk batch",
                        "chunk_numbers": chunk_numbers,
                        "document_id": self.document_id,
                        "org_id": self.org_id,
                        "project_id": self.project_id,
                        "batch_size": len(batch_chunks),
                    })

                    #  Embed the batch of texts
                    texts = [chunk.text for chunk in batch_chunks]
                    em_vectors: List[SparseEmbedding] = await sparse_embedder.embed_batch(texts)

                    #  Concurrently save each sparse embedding to Redis (uncomment if needed)
                    # redis_tasks = [
                    #     self._sparse_embedding_redis.add_sparse_embedding_temporary(
                    #         document_id=self.document_id,
                    #         chunk_number=chunk.chunk_number,
                    #         sparse_embedding=vector,
                    #     )
                    #     for chunk, vector in zip(batch_chunks, em_vectors)
                    # ]
                    # await asyncio.gather(*redis_tasks)

                    # Append to the final results list
                    for chunk, vector in zip(batch_chunks, em_vectors):
                        chs_sparse_embeddings.append(
                            ChunkSparseEmbedding(
                                chunk_id=chunk.chunk_id,
                                chunk_number=chunk.chunk_number,
                                embedding=vector,
                            )
                        )

                except Exception as e:
                    logger.error({
                        "message": "Failed to run sparse agent for batch",
                        "chunk_numbers": chunk_numbers,
                        "document_id": self.document_id,
                        "org_id": self.org_id,
                        "project_id": self.project_id,
                        "error": str(e),
                    })
                    raise e

            # Sort and prepare final results
            chs_sparse_embeddings.sort(key=lambda x: x.chunk_number)

            # Upload sparse embeddings
            data_for_minio = {"data": [chunk.model_dump_json() for chunk in chs_sparse_embeddings]}
            minio_file_name = MinioConstant.SPARSE_EMBEDDING_OUTPUT_FILE

            await self.minio_helper.upload_json(json_file_name=minio_file_name, json_data=data_for_minio, document_id=self.document_id)
            await self._dig_redis.update_status(dig_node=GRedisConstant.SPARSE_EMBEDDING_NODE, status=GRedisConstant.DIG_NODE_STATUS_COMPLETED)

            return {"chunks_sparse_embeddings": chs_sparse_embeddings}

        except Exception as e:
            logger.error({"message": "Failed to run sparse agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e), "traceback": traceback.format_exc()})
            raise e

    async def _lexical_engine_agent(self, state: DIGState):
        try:
            chunks = state["chunks"]
            lexical_engine = LexicalEngine()

            le_chunks: List[LEChunk] = []
            for chunk in chunks:
                le_chunks.append(LEChunk(chunk_id=chunk.chunk_id, chunk_number=chunk.chunk_number, text=chunk.text))
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, lexical_engine.run_lexical_engine, le_chunks)

            await self.minio_helper.upload_json(json_file_name=MinioConstant.LEXICAL_ENGINE_OUTPUT_FILE, json_data=result.model_dump(), document_id=self.document_id)

            lexical_engine_data = result
            # await self._dig_redis.update_status(dig_node=GRedisConstant.LEXICAL_ENGINE_NODE, status=GRedisConstant.DIG_NODE_STATUS_COMPLETED)

            return {"lexical_engine_data": lexical_engine_data}
        except Exception as e:
            logger.error({"message": "Failed to run lexical engine agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            raise e

    async def _vector_database_agent(self, state: DIGState):
        try:
            chunks = state["chunks"]
            chunks_embeddings = state["chunks_embeddings"]
            chunks_sparse_embeddings = state["chunks_sparse_embeddings"]

            ep_model_key = state["ep_model_key"]

            await self.injector.inject(model_key=ep_model_key, document_id=self.document_id, chunks=chunks, chunk_embeddings=chunks_embeddings, chunk_sparse_embeddings=chunks_sparse_embeddings)
            # await self._dig_redis.update_status(dig_node=GRedisConstant.VECTOR_DATABASE_NODE, status=GRedisConstant.DIG_NODE_STATUS_COMPLETED)
            return {}
        except Exception as e:
            logger.error({"message": "Failed to run chunks processor agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            raise e

    async def _graph_database_agent(self, state: DIGState):
        try:
            chunks = state["chunks"]
            logger.info({"message": "Creating graph database", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})

            await self.n4j_chunk_db.create_multiple(self.document_id, self.document_readable_id, chunks)

            lexical_engine_data = state["lexical_engine_data"]
            if lexical_engine_data is not None:
                logger.info({"message": "Creating graph database edges", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                semantic_result = self.to_lexical_semantic_result(lexical_engine_data)
                await self.n4j_chunk_db.create_edges_by_lexical_engine_data(self.document_id, self.document_readable_id, semantic_result)

            chunk_tag_results = state["chunk_tag_results"]
            if chunk_tag_results is not None:
                logger.info({"message": "Creating graph database edges", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
                tags = await self._llm_agent_process(chunk_results=chunk_tag_results, chunks=chunks)

                # Upload LLM tags
                tags_json = [tag.model_dump_json() for tag in tags]
                await self.minio_helper.upload_json(json_file_name=MinioConstant.LLM_TAG_RESPONSE, json_data={"data": tags_json}, document_id=self.document_id)
                # await self._dig_redis.update_status(dig_node=GRedisConstant.GRAPH_DATABASE_NODE, status=GRedisConstant.DIG_NODE_STATUS_COMPLETED)

            return {}
        except Exception as e:
            logger.error({"message": "Failed to run graph database agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            raise e

    async def _similarity_sync_agent(self, state: DIGState):
        try:
            pass
            # ep_model_key = state["ep_model_key"]
            # chunks = state["chunks"]
            # chunk_ids = [chunk.chunk_id for chunk in chunks]

            # result: dict[str, list[ChunkDenseVectorScore]] = await self.qdrant_similarity.get_similar_chunks(model_key=ep_model_key, document_id=self.document_id, chunk_ids=chunk_ids, top_k=3)

            # n4j_similarity_edges: list[N4jChunkEdge] = []

            # for from_chunk_id, obj in result.items():
            #     for cs in obj:
            #         n4j_similarity_edges.append(N4jChunkEdge(from_chunk_id=from_chunk_id, to_chunk_id=cs.chunk_id, edge_name=GNeo4jEdges.VECTOR_SIMILARITY, label="vector_similarity", weight=cs.score))

            # logger.info({"message": "Creating vector similarity edges", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id})
            # await self.n4j_chunk_db.create_edges(self.document_id, n4j_similarity_edges)
            # # await self._dig_redis.update_status(dig_node=GRedisConstant.SIMILARITY_SYNC_NODE, status=GRedisConstant.DIG_NODE_STATUS_COMPLETED)
            # return {}
        except Exception as e:
            logger.error({"message": "Failed to run similarity sync agent", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            raise e

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

        n4j_nex_prev_edges: list[N4jChunkEdge] = []
        n4j_reference_edges: list[N4jChunkEdge] = []

        tag_data: dict[str, dict[str, float]] = {}
        for tag, chunk_confidences in tag_map.items():
            tag_data[tag] = {chunk_id: conf for chunk_id, conf in chunk_confidences}

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

        n4j_nex_prev_edges_json = [edge.model_dump_json() for edge in n4j_nex_prev_edges]
        n4j_reference_edges_json = [edge.model_dump_json() for edge in n4j_reference_edges]

        # UPLOAD TO MINIO
        await self.minio_helper.upload_json(json_file_name=MinioConstant.N4J_EDGES_TAG_OUTPUT, json_data=tag_data, document_id=self.document_id)
        await self.minio_helper.upload_json(json_file_name=MinioConstant.N4J_EDGES_NEXT_PREV_OUTPUT, json_data={"data": n4j_nex_prev_edges_json}, document_id=self.document_id)
        await self.minio_helper.upload_json(json_file_name=MinioConstant.N4J_EDGES_REFERENCE_OUTPUT, json_data={"data": n4j_reference_edges_json}, document_id=self.document_id)

        # Merge TO NEO4J
        await self.n4j_chunk_db.create_semantic_nodes_and_edges(
            document_id=self.document_id,
            node_type=GN4jNodes.TAG,
            edge_type=GNeo4jEdges.HAS_TAG,
            value_field=common.N4jTagInterface.value,
            data=tag_data,
        )
        await self.n4j_chunk_db.create_edges(self.document_id, n4j_nex_prev_edges)
        await self.n4j_chunk_db.create_edges(self.document_id, n4j_reference_edges)

        return all_chunk_tags

    def to_lexical_semantic_result(self, result: LexicalResult) -> LexicalSemanticResult:
        """
        Converts LexicalResult (chunk↔chunk edges) into LexicalSemanticResult
        (value → {chunk_id: weight} maps) without touching LexicalEngine at all.
        """

        edge_type_to_field = {
            GNeo4jEdges.SHARES_ENTITY: "entity_map",
            GNeo4jEdges.SHARES_CONCEPT: "concept_map",
            GNeo4jEdges.SHARES_KEYWORD: "keyword_map",
            GNeo4jEdges.SHARES_PHRASE: "phrase_map",
        }

        # {field_name: {label: {chunk_id: best_weight}}}
        maps: dict[str, dict[str, dict[str, float]]] = {
            "entity_map": defaultdict(dict),
            "concept_map": defaultdict(dict),
            "keyword_map": defaultdict(dict),
            "phrase_map": defaultdict(dict),
        }

        for edge in result.edges:
            field = edge_type_to_field.get(edge.edge_type)
            if field is None:
                continue  # SHARES_ACRONYM handled via acronyms dict, skip others

            label_map = maps[field][edge.label]

            # Each edge is (source, target, weight) — assign weight to both chunks
            # take max if chunk already seen from another edge
            label_map[edge.source] = max(label_map.get(edge.source, 0.0), edge.weight)
            label_map[edge.target] = max(label_map.get(edge.target, 0.0), edge.weight)

        return LexicalSemanticResult(
            filtered_noise=result.filtered_noise,
            entity_map=dict(maps["entity_map"]),
            concept_map=dict(maps["concept_map"]),
            keyword_map=dict(maps["keyword_map"]),
            phrase_map=dict(maps["phrase_map"]),
            acronyms=result.acronyms,  # already correct shape
        )
