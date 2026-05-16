from app.core.schemas.chunk_schema import ChunkPrevNextVecSimilaritySchema, ChunkPrevNextSchema, ChunkVecSimilarity
from ..schemas.provider_schema import QueryProviderSchema, LLMProviderSchema
from .prompts.answer_prompt import BASIC_ANSWER_PROMPT, SMART_ANSWER_PROMPT
from qdrant_client.conversions.common_types import QueryResponse
from ..provider import WorkflowEmbedder, WorkflowSparseEmbedder
from app.core.lexical_engine.query import LexicalEngineQuery
from typing import TypedDict, Annotated, Dict, cast, Tuple
from app.core.qdrant.retrieval import QDrantRetrieval
from ..provider import WorkflowReranker, WorkflowLLM
from langgraph.graph import StateGraph, START, END
from app.core.schemas import query_schema as qs
from langchain_core.documents import Document
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
QUICK_QUERY_RERANKER_AGENT = " quick_query_reranker_agent"
QUICK_QUERY_ANSWER_AGENT = "quick_query_answer_agent"
SMART_QUERY_RERANKER_AGENT = "smart_query_reranker_agent"
SMART_QUERY_ANSWER_AGENT = "smart_query_answer_agent"
EXPERT_QUERY_RERANKER_AGENT = "expert_query_reranker_agent"
EXPERT_QUERY_ANSWER_AGENT = "expert_query_answer_agent"


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
    chunks: list[ChunkPrevNextVecSimilaritySchema] | list[ChunkPrevNextSchema] | None
    reranked_chunks: list[ChunkPrevNextSchema] | list[ChunkPrevNextVecSimilaritySchema] | None
    vec_similar_with_prev_next: list[ChunkPrevNextSchema] | None
    query_dense_embedding: Annotated[list[float] | None, merge_optional]
    query_sparse_embedding: Annotated[SparseEmbedding | None, merge_optional]

    answer: str | dict | None


class DocumentQueryGraph():
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.q_retrieval = QDrantRetrieval(org_id=org_id, project_id=project_id)
        self._lexical_engine = LexicalEngineQuery()
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

            graph.add_node(QUICK_QUERY_RERANKER_AGENT, self._qq_reranker)
            graph.add_node(SMART_QUERY_RERANKER_AGENT, self._sq_reranker)
            graph.add_node(EXPERT_QUERY_RERANKER_AGENT, self._eq_reranker)

            graph.add_node(QUICK_QUERY_ANSWER_AGENT, self._qq_answer)
            graph.add_node(SMART_QUERY_ANSWER_AGENT, self._sq_answer)
            graph.add_node(EXPERT_QUERY_ANSWER_AGENT, self._eq_answer)

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

            graph.add_edge(QUICK_QUERY_AGENT, QUICK_QUERY_RERANKER_AGENT)
            graph.add_edge(SMART_QUERY_AGENT, SMART_QUERY_RERANKER_AGENT)
            graph.add_edge(EXPERT_QUERY_AGENT, EXPERT_QUERY_RERANKER_AGENT)

            graph.add_edge(QUICK_QUERY_RERANKER_AGENT, QUICK_QUERY_ANSWER_AGENT)
            graph.add_edge(SMART_QUERY_RERANKER_AGENT, SMART_QUERY_ANSWER_AGENT)
            graph.add_edge(EXPERT_QUERY_RERANKER_AGENT, EXPERT_QUERY_ANSWER_AGENT)

            graph.add_edge(QUICK_QUERY_ANSWER_AGENT, END)
            graph.add_edge(SMART_QUERY_ANSWER_AGENT, END)
            graph.add_edge(EXPERT_QUERY_ANSWER_AGENT, END)

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

            print("Total points:", len(result.points))
            print("Points:", result.points)

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

            chunk_ids: set[Tuple[str, float]] = set()

            for point in points:
                score = point.score
                if score < Env.GTE_QDRANT_POINT_SCORE_THRESHOLD:
                    continue

                payload = point.payload
                if payload is None:
                    continue

                text = payload.get("text")
                chunk_id = payload.get("chunk_id")
                if text is None or chunk_id is None:
                    continue

                chunk_ids.add((chunk_id, score))

            if len(chunk_ids) == 0:
                raise Exception("No chunk ids found")
            document_id = state["document_id"]

            chunks: list[ChunkPrevNextSchema] = await self._chunk_n4j.get_prev_next_chunks(chunk_id_scores=[(c[0], c[1]) for c in chunk_ids], document_id=document_id)

            return {"chunks": chunks}
        except Exception as e:
            logger.error({"message": "Failed in quick query", "error": str(e)})

    async def _smart_query(self, state: DQGState):
        try:
            logger.info({"message": "Smart query"})
            points = state["points"]

            if points is None or len(points) == 0:
                raise Exception("No points found")

            chunk_ids: set[Tuple[str, float]] = set()

            for point in points:
                score = point.score
                if score < Env.GTE_QDRANT_POINT_SCORE_THRESHOLD:
                    continue

                payload = point.payload
                if payload is None:
                    continue

                text = payload.get("text")
                chunk_id = payload.get("chunk_id")
                if text is None or chunk_id is None:
                    continue

                chunk_ids.add((chunk_id, score))

            if len(chunk_ids) == 0:
                raise Exception("No chunk ids found")
            document_id = state["document_id"]

            prev_next_chunks: list[ChunkPrevNextSchema] = await self._chunk_n4j.get_prev_next_chunks(chunk_id_scores=[(c[0], c[1]) for c in chunk_ids], document_id=document_id)

            vec_similar_chunks: Dict[str, ChunkVecSimilarity] = await self._chunk_n4j.get_vector_similar_chunks(chunk_id_scores=[(c[0], c[1]) for c in chunk_ids], document_id=document_id, gte__vector_score=Env.GTE_EDGE_VECTOR_SIMILAR_THRESHOLD)

            print("\n\n [Smart]: Vector Similar Chunks:\n", vec_similar_chunks)

            chunks: list[ChunkPrevNextVecSimilaritySchema] = []

            for chunk in prev_next_chunks:
                c = ChunkPrevNextVecSimilaritySchema(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    chunk_number=chunk.chunk_number,
                    weight=chunk.weight,
                    point_score=chunk.point_score,
                    prev_chunk=chunk.prev_chunk,
                    next_chunk=chunk.next_chunk,
                )

                vector_similar = vec_similar_chunks[chunk.chunk_id]
                if vector_similar is not None:
                    c.vector_similar_chunks = vector_similar.vector_similar_chunks

                chunks.append(c)

            return {"chunks": chunks}
        except Exception as e:
            logger.error({"message": "Failed in smart query", "error": str(e)})
            raise e

    async def _expert_query(self, state: DQGState):
        try:
            logger.info({"message": "Expert query"})
            query = state["query"]
            query_depth: qs.QueryDepth = state["query_depth"]
            if query_depth == qs.QueryDepth.ADVANCED:
                analysis = self._lexical_engine.analyze_query(query)
                return {"answer": analysis.model_dump()}

        except Exception as e:
            logger.error({"message": "Failed in expert query", "error": str(e)})

    async def _qq_reranker(self, state: DQGState):
        try:
            query = state["query"]
            chunks: list[ChunkPrevNextSchema] = cast(list[ChunkPrevNextSchema], state["chunks"])
            top_k = state["top_k"]

            if chunks is None or len(chunks) == 0:
                raise Exception("No chunks found")

            providers = state["providers"]
            reranker_provider = providers.reranker.provider
            reranker_model = providers.reranker.model

            reranker = WorkflowReranker().reranker(model=reranker_model, provider=reranker_provider)

            # index chunks by chunk_id for O(1) lookup
            chunk_map: dict[str, ChunkPrevNextSchema] = {chunk.chunk_id: chunk for chunk in chunks}

            docs: list[Document] = []
            for chunk in chunks:
                docs.append(Document(
                    page_content=chunk.text,
                    metadata={"chunk_id": chunk.chunk_id}
                ))

            rerank_docs = reranker.rerank(query=query, docs=docs, top_k=top_k)

            reranked_chunks: list[ChunkPrevNextSchema] = []
            for doc in rerank_docs:
                chunk = chunk_map[doc.metadata["chunk_id"]]
                reranked_chunks.append(chunk)

            seen_ids: set[str] = set()
            deduped: list[ChunkPrevNextSchema] = []

            # So we can't select the chunk if it has been selected before as a prev/next chunk
            for chunk in reranked_chunks:
                if chunk.chunk_id in seen_ids:
                    continue
                deduped.append(chunk)
                seen_ids.add(chunk.chunk_id)
                if chunk.prev_chunk:
                    seen_ids.add(chunk.prev_chunk.chunk_id)
                if chunk.next_chunk:
                    seen_ids.add(chunk.next_chunk.chunk_id)

            # sort by weight descending
            deduped = sorted(deduped, key=lambda x: x.point_score, reverse=True)

            print("\n\n [Quick] Final reranked chunks: ", deduped)

            return {"reranked_chunks": deduped}
        except Exception as e:
            logger.error({"message": "Failed to reranker", "error": str(e)})
            raise e

    async def _qq_answer(self, state: DQGState):
        try:
            reranked_chunks: list[ChunkPrevNextSchema] = cast(list[ChunkPrevNextSchema], state["reranked_chunks"])
            if reranked_chunks is None or len(reranked_chunks) == 0:
                raise Exception("No reranked chunks found")

            query = state["query"]
            providers = state["providers"]
            llm_provider = providers.llm

            answer = await self._qq_llm_call(query=query, provider=llm_provider, reranked_chunks=reranked_chunks)
            return {"answer": answer}
        except Exception as e:
            logger.error({"message": "Failed to answer", "error": str(e)})
            raise e

    async def _qq_llm_call(self, query: str, provider: LLMProviderSchema, reranked_chunks: list[ChunkPrevNextSchema]) -> str:
        try:
            llm_provider = provider.provider
            api_key = provider.api_key
            model = provider.model
            chunks_str = self._qq_format_chunks(reranked_chunks)

            print("\n\n [Quick] Final chunks string for LLM :\n", chunks_str)

            prompt = BASIC_ANSWER_PROMPT.format(context=chunks_str, query=query)
            llm = WorkflowLLM.llm(provider=llm_provider, api_key=api_key, model=model)
            response = await llm.ainvoke(prompt=prompt)

            return response.content
        except Exception as e:
            logger.error({"message": "Failed to llm call", "error": str(e)})
            raise e

    def _qq_format_chunks(self, chunks: list[ChunkPrevNextSchema]) -> str:
        main_chunk_ids = {chunk.chunk_id for chunk in chunks}
        total = len(chunks)
        blocks = []
        for i, chunk in enumerate(chunks):
            block = self._qq_format_single_chunk(chunk, index=i + 1, total=total, skip_ids=main_chunk_ids)
            blocks.append(block)
        return "\n\n".join(blocks)

    def _qq_format_single_chunk(self, chunk: ChunkPrevNextSchema, index: int, total: int, skip_ids: set[str]) -> str:
        if chunk.weight >= 0.8:
            relevance_label = "High Relevance"
        elif chunk.weight >= 0.5:
            relevance_label = "Medium Relevance"
        else:
            relevance_label = "Low Relevance"

        lines = [f"[Chunk {index} of {total}] (Weight: {chunk.weight:.2f} — {relevance_label})"]

        if chunk.prev_chunk and chunk.prev_chunk.chunk_id not in skip_ids:
            lines.append(f"\n[Previous Context]:\n{chunk.prev_chunk.text}")

        lines.append(f"\n[Main — {relevance_label}]:\n{chunk.text}")

        if chunk.next_chunk and chunk.next_chunk.chunk_id not in skip_ids:
            lines.append(f"\n[Next Context]:\n{chunk.next_chunk.text}")

        lines.append("\n" + "─" * 40)
        return "\n".join(lines)

    async def _sq_reranker(self, state: DQGState):
        try:
            query = state["query"]
            chunks: list[ChunkPrevNextVecSimilaritySchema] = cast(list[ChunkPrevNextVecSimilaritySchema], state["chunks"])
            if chunks is None or len(chunks) == 0:
                raise Exception("No chunks found")

            top_k = state["top_k"]

            if not chunks:
                raise Exception("No chunks found")

            providers = state["providers"]
            reranker_provider = providers.reranker.provider
            reranker_model = providers.reranker.model

            reranker = WorkflowReranker().reranker(model=reranker_model, provider=reranker_provider)

            # index chunks by chunk_id for O(1) lookup
            chunk_map: dict[str, ChunkPrevNextVecSimilaritySchema] = {chunk.chunk_id: chunk for chunk in chunks}

            docs: list[Document] = []
            for chunk in chunks:
                docs.append(Document(
                    page_content=chunk.text,
                    metadata={"chunk_id": chunk.chunk_id}
                ))

            rerank_docs = reranker.rerank(query=query, docs=docs, top_k=top_k)

            reranked_chunks: list[ChunkPrevNextVecSimilaritySchema] = []
            for doc in rerank_docs:
                chunk = chunk_map[doc.metadata["chunk_id"]]
                reranked_chunks.append(chunk)

            query_depth: qs.QueryDepth = state["query_depth"]
            vec_similar_with_prev_next: list[ChunkPrevNextSchema] = []

            if query_depth is qs.QueryDepth.ADVANCED:
                try:
                    chunk_id_scores: list[tuple[str, float]] = []
                    for chunk in reranked_chunks:
                        if chunk.vector_similar_chunks:
                            for vc in chunk.vector_similar_chunks:
                                chunk_id_scores.append((vc.chunk_id, vc.weight))

                    if chunk_id_scores:
                        res = await self._chunk_n4j.get_prev_next_chunks(
                            chunk_id_scores=chunk_id_scores,
                            document_id=state["document_id"]
                        )
                        vec_similar_with_prev_next.extend(res)
                except Exception as e:
                    logger.error({"message": "Failed to get prev/next for vector similar chunks", "error": str(e)})

            seen_ids: set[str] = set()
            deduped: list[ChunkPrevNextVecSimilaritySchema] = []

            # So we can't select the chunk if it has been selected before as a prev/next chunk
            for chunk in reranked_chunks:
                if chunk.chunk_id in seen_ids:
                    continue
                deduped.append(chunk)
                seen_ids.add(chunk.chunk_id)
                if chunk.prev_chunk:
                    seen_ids.add(chunk.prev_chunk.chunk_id)
                if chunk.next_chunk:
                    seen_ids.add(chunk.next_chunk.chunk_id)

            # sort by weight descending
            deduped = sorted(deduped, key=lambda x: x.point_score, reverse=True)

            print("\n\n [Smart] Final reranked chunks: ", deduped)

            return {"reranked_chunks": deduped, "vec_similar_with_prev_next": vec_similar_with_prev_next}

        except Exception as e:
            logger.error({"message": "Failed to sq_reranker", "error": str(e)})
            raise e

    async def _sq_answer(self, state: DQGState):
        try:
            reranked_chunks: list[ChunkPrevNextVecSimilaritySchema] = cast(
                list[ChunkPrevNextVecSimilaritySchema], state["reranked_chunks"]
            )
            if not reranked_chunks:
                raise Exception("No reranked chunks found")

            query = state["query"]
            query_depth: qs.QueryDepth = state["query_depth"]
            vec_similar_with_prev_next: list[ChunkPrevNextSchema] = state["vec_similar_with_prev_next"] or []
            providers = state["providers"]

            answer = await self._sq_llm_call(
                query=query,
                provider=providers.llm,
                reranked_chunks=reranked_chunks,
                query_depth=query_depth,
                vec_similar_with_prev_next=vec_similar_with_prev_next,
            )
            return {"answer": answer}

        except Exception as e:
            logger.error({"message": "Failed to sq_answer", "error": str(e)})
            raise e

    async def _sq_llm_call(
        self,
        query: str,
        provider: LLMProviderSchema,
        reranked_chunks: list[ChunkPrevNextVecSimilaritySchema],
        query_depth: qs.QueryDepth,
        vec_similar_with_prev_next: list[ChunkPrevNextSchema],
    ) -> str:
        try:
            llm = WorkflowLLM.llm(provider=provider.provider, api_key=provider.api_key, model=provider.model)
            chunks_str = self._sq_format_chunks(
                chunks=reranked_chunks,
                query_depth=query_depth,
                vec_similar_with_prev_next=vec_similar_with_prev_next,
            )
            prompt = SMART_ANSWER_PROMPT.format(context=chunks_str, query=query)

            print("\n\n [Smart] Final chunks string for LLM :\n", chunks_str)

            response = await llm.ainvoke(prompt=prompt)
            return response.content

        except Exception as e:
            logger.error({"message": "Failed to sq_llm_call", "error": str(e)})
            raise e

    def _sq_format_chunks(
        self,
        chunks: list[ChunkPrevNextVecSimilaritySchema],
        query_depth: qs.QueryDepth,
        vec_similar_with_prev_next: list[ChunkPrevNextSchema],
    ) -> str:
        # build a map of advanced vec similar chunks by chunk_id for O(1) lookup
        adv_map: dict[str, ChunkPrevNextSchema] = {c.chunk_id: c for c in vec_similar_with_prev_next}

        # collect all chunk_numbers and texts into a single number -> (text, label) map
        number_to_entry: dict[int, tuple[str, str]] = {}

        for chunk in chunks:
            # main chunk
            number_to_entry.setdefault(chunk.chunk_number, (chunk.text, "[Main]"))

            # prev/next of main
            if chunk.prev_chunk:
                number_to_entry.setdefault(chunk.prev_chunk.chunk_number, (chunk.prev_chunk.text, "[Previous Context]"))
            if chunk.next_chunk:
                number_to_entry.setdefault(chunk.next_chunk.chunk_number, (chunk.next_chunk.text, "[Next Context]"))

            # vector similar chunks
            if chunk.vector_similar_chunks:
                for vc in chunk.vector_similar_chunks:
                    if vc.chunk_number not in number_to_entry:
                        if query_depth == qs.QueryDepth.ADVANCED and vc.chunk_id in adv_map:
                            # advanced: use the full chunk with its prev/next
                            full = adv_map[vc.chunk_id]
                            number_to_entry.setdefault(full.chunk_number, (full.text, "[Vector Similar]"))
                            if full.prev_chunk:
                                number_to_entry.setdefault(full.prev_chunk.chunk_number, (full.prev_chunk.text, "[Vector Similar Previous Context]"))
                            if full.next_chunk:
                                number_to_entry.setdefault(full.next_chunk.chunk_number, (full.next_chunk.text, "[Vector Similar Next Context]"))
                        else:
                            # standard: just the vector similar text
                            number_to_entry.setdefault(vc.chunk_number, (vc.text, "[Vector Similar]"))

        # merge contiguous chunk_numbers into sequences
        sorted_numbers = sorted(number_to_entry.keys())
        sequences: list[list[int]] = []
        current: list[int] = [sorted_numbers[0]]

        for num in sorted_numbers[1:]:
            if num == current[-1] + 1:
                current.append(num)
            else:
                sequences.append(current)
                current = [num]
        sequences.append(current)

        # render each sequence as one block
        blocks = []
        for seq in sequences:
            lines = []
            for num in seq:
                text, label = number_to_entry[num]
                lines.append(f"{label}:\n{text}")
            blocks.append("\n\n".join(lines) + "\n" + "─" * 40)

        return "\n\n".join(blocks)

    async def _eq_reranker(self, state: DQGState):
        try:
            pass
        except Exception as e:
            logger.error({"message": "Failed to eq_reranker", "error": str(e)})
            raise e

    async def _eq_answer(self, state: DQGState):
        try:
            pass
        except Exception as e:
            logger.error({"message": "Failed to eq_answer", "error": str(e)})
            raise e

    def _effective_top_k(self, chunks: list[ChunkPrevNextSchema], desired_results: int) -> int:
        has_prev = sum(1 for c in chunks if c.prev_chunk)
        has_next = sum(1 for c in chunks if c.next_chunk)
        avg_neighbors = (has_prev + has_next) / len(chunks)
        # avg_neighbors ~2 means each chunk brings ~3x content
        return max(1, round(desired_results / (1 + avg_neighbors)))
