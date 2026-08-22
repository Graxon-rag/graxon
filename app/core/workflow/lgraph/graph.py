from .document_react_query_graph import DocumentQueryReActGraph, ReActDQGState
from ...services.project_config_service import ProjectConfigService
from .document_inject_graph import DocumentInjectGraph, DIGState
from app.core.schemas.query_schema import QueryDepth, QueryType
from .document_query_graph import DocumentQueryGraph, DQGState
from .prompts.answer_prompt import DEFAULT_ANSWER_RESPONSE
from app.core.schemas.query_schema import GQuery
from ...libs.embedding_lib import EmbeddingLib
from ...schemas import processor_schema as ps
from ...schemas import chunk_schema as cs
from app.utils.logger import logger
from typing import AsyncGenerator
from typing import List, Any
import json
import uuid


class Graph:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self._pcs = ProjectConfigService(org_id=self.org_id, project_id=self.project_id)

    async def inject_document(self, cp: ps.CommonParams, chunks: List[cs.Chunk]):
        try:
            project_config = await self._pcs.get_with_details_by_project(is_external_call=False)
            if project_config is None:
                raise Exception("Project config not found")
            embedder_provider = project_config.embedding_model
            if embedder_provider is None:
                raise Exception("Embedder provider not found")

            ep_model_key = EmbeddingLib.get_model_key(embedder_provider.provider.value, embedder_provider.dimension)

            request_id = str(uuid.uuid4())
            graph = DocumentInjectGraph(cp)
            workflow = graph.build_graph()
            initial_state: DIGState = {
                "request_id": request_id,
                "org_id": self.org_id,
                "project_id": self.project_id,
                "document_id": cp.doc_id,
                "project_config": project_config,
                "ep_model_key": ep_model_key,
                "chunks": chunks,
                "tags": [],
                "chunk_tag_results": [],
                "lexical_engine_data": None,
                "chunks_embeddings": [],
                "chunks_sparse_embeddings": []
            }

            if workflow is None:
                raise Exception("Workflow is None")

            temp_path = None

            try:
                result = await workflow.ainvoke(initial_state)
                temp_path = result.get("temp_path")
                return result
            except Exception as e:
                logger.error({"message": "Failed to inject document", "error": str(e)})
                raise e
            finally:
                # Delete temp folder
                import shutil
                if temp_path:
                    shutil.rmtree(temp_path, ignore_errors=True)
                    logger.info({"message": "Deleted temp folder", "path": temp_path})

        except Exception as e:
            logger.error({"message": "Failed to inject document", "error": str(e)})
            raise e

    async def query_documents(self, query: GQuery):
        try:
            print("Query:", query)
            project_config = await self._pcs.get_with_details_by_project(is_external_call=False)
            if project_config is None:
                raise Exception("Project config not found")
            embedder_provider = project_config.embedding_model
            if embedder_provider is None:
                raise Exception("Embedder provider not found")

            ep_model_key = EmbeddingLib.get_model_key(embedder_provider.provider.value, embedder_provider.dimension)

            graph = DocumentQueryGraph(org_id=self.org_id, project_id=self.project_id)
            workflow = graph.build_graph()
            if workflow is None:
                raise Exception("Workflow is None")

            request_id = str(uuid.uuid4())
            initial_state: DQGState = {
                "request_id": request_id,
                "org_id": self.org_id,
                "project_id": self.project_id,
                "project_config": project_config,
                "ep_model_key": ep_model_key,
                "query": query.query,
                "queries": [query.query],
                "top_k": query.top_k,
                "query_type": query.query_type,
                "query_depth": query.query_depth,
                "document_id": query.document_id,
                "points": None,
                "chunks": [],
                "reranked_chunks": [],
                "vec_similar_with_prev_next": [],
                "eq_analysis": None,
                "eq_lexical_engine_chunk_ids": None,
                "query_dense_embedding": None,
                "query_sparse_embedding": None,
                "answer": None
            }
            result = await workflow.ainvoke(initial_state)
            answer = result.get("answer") or DEFAULT_ANSWER_RESPONSE
            reranked_chunks = result.get("reranked_chunks")
            metadata = [self._safe_serialize(c) for c in reranked_chunks or []]

            response = {"answer": answer, "query": query.query, "metadata": metadata}

            if query.query_type == QueryType.EXPERT and query.query_depth == QueryDepth.ADVANCED:
                response["lexical_engine_analysis"] = self._safe_serialize(result.get("eq_analysis"))

            if query.query_type == QueryType.EXPERT:
                response["lexical_engine_chunk_ids"] = [
                    {"chunk_id": chunk_id, "score": score}
                    for chunk_id, score in (result.get("eq_lexical_engine_chunk_ids") or [])
                ]
            return response
        except Exception as e:
            logger.error({"message": "Failed to query", "error": str(e)})
            return DEFAULT_ANSWER_RESPONSE

    def _safe_serialize(self, c):
        if hasattr(c, "model_dump"):          # Pydantic v2
            return c.model_dump(mode="json")
        elif hasattr(c, "dict"):              # Pydantic v1
            return c.dict()
        elif isinstance(c, dict):             # Already a dict
            return c
        else:                                 # Fallback — any object
            return vars(c)

    async def stream_query_documents(self, query: GQuery) -> AsyncGenerator[str, None]:
        def _sse(event: str, data: Any) -> str:
            """Helper to format outputs as Server-Sent Events."""
            data_str = json.dumps(data) if not isinstance(data, str) else data

            # CRITICAL: per the SSE spec, a single "data:" field cannot contain a
            # literal newline — a blank line inside the payload is indistinguishable
            # from the frame terminator ("\n\n") that marks the end of an event.
            # Any payload with embedded newlines (e.g. multi-paragraph model output)
            # MUST be split into multiple "data:" lines, one per line of content,
            # which the client then rejoins with "\n". Skipping this silently
            # truncates the event at the first embedded blank line.
            data_lines = data_str.split("\n")
            data_field = "\n".join(f"data: {line}" for line in data_lines)

            return f"event: {event}\n{data_field}\n\n"

        # Buffers text per LLM call (keyed by run_id) until we know, from
        # on_chat_model_end, whether that turn ended in tool_calls (-> reasoning)
        # or not (-> final answer). This is the ONLY reliable signal, since
        # _agent_node runs its whole ReAct loop as a single graph node -- there's
        # no node-name distinction between reasoning turns and the final turn.
        turn_buffers: dict[str, str] = {}

        try:
            print("Stream Query:", query)
            project_config = await self._pcs.get_with_details_by_project(is_external_call=False)
            if project_config is None:
                raise Exception("Project config not found")

            embedder_provider = project_config.embedding_model
            if embedder_provider is None:
                raise Exception("Embedder provider not found")

            ep_model_key = EmbeddingLib.get_model_key(embedder_provider.provider.value, embedder_provider.dimension)

            graph = DocumentQueryReActGraph(org_id=self.org_id, project_id=self.project_id)
            workflow = graph.build_graph()
            if workflow is None:
                raise Exception("Workflow is None")

            initial_state: ReActDQGState = {
                "request_id": str(uuid.uuid4()),
                "org_id": self.org_id,
                "project_id": self.project_id,
                "project_config": project_config,
                "ep_model_key": ep_model_key,
                "query": query.query,
                "top_k": query.top_k,
                "query_type": query.query_type,
                "query_depth": query.query_depth,
                "document_id": query.document_id,
                "queries": [query.query],
                "metadata": [],
                "eq_analysis": None,
                "eq_lexical_engine_chunk_ids": None,
                "answer": None
            }

            async for event in workflow.astream_events(initial_state, version="v2"):
                kind = event["event"]
                run_id = event.get("run_id")

                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]  # type: ignore

                    # Non-text reasoning fields (if your model/provider populates
                    # them) can still stream live immediately -- they're
                    # unambiguously reasoning regardless of tool_calls.
                    reasoning = getattr(chunk, "additional_kwargs", {}).get("reasoning_content")
                    if reasoning:
                        yield _sse("thinking", reasoning)

                    if chunk.content:
                        content_str = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                        # Buffer -- don't emit yet, we don't know this turn's
                        # classification until on_chat_model_end.
                        turn_buffers[run_id] = turn_buffers.get(run_id, "") + content_str

                elif kind == "on_chat_model_end":
                    text = turn_buffers.pop(run_id, "")
                    if text:
                        output = event["data"]["output"]  # type: ignore
                        has_tool_calls = bool(getattr(output, "tool_calls", None))
                        # Tool-planning turn -> reasoning. Plain-text-only turn
                        # (including the forced final-answer call, which uses
                        # base_llm with no tools bound) -> real answer.
                        if has_tool_calls:
                            yield _sse("thinking", text)
                        else:
                            yield _sse("token", text)

                elif kind == "on_tool_start":
                    yield _sse("tool_call", {"name": event["name"], "input": event["data"].get("input")})

                elif kind == "on_tool_end":
                    output = event["data"].get("output")
                    output_str = getattr(output, "content", str(output))
                    yield _sse("tool_result", {"name": event["name"], "output": output_str})

                elif kind == "on_chain_end" and event["name"] == "agent_node":
                    output = event["data"].get("output") or {}
                    metadata_payload = {
                        "chunks": output.get("metadata") or [],
                        "lexical_engine_analysis": None
                    }
                    if query.query_type == QueryType.EXPERT and query.query_depth == QueryDepth.ADVANCED:
                        metadata_payload["lexical_engine_analysis"] = self._safe_serialize(output.get("eq_analysis"))
                    if query.query_type == QueryType.EXPERT:
                        metadata_payload["lexical_engine_chunk_ids"] = [
                            {"chunk_id": chunk_id, "score": score}
                            for chunk_id, score in (output.get("eq_lexical_engine_chunk_ids") or [])
                        ]
                    yield _sse("metadata", metadata_payload)

        except Exception as e:
            logger.error({"message": "Failed to stream query", "error": str(e)})
            yield _sse("error", str(e))
        finally:
            yield _sse("done", "")
