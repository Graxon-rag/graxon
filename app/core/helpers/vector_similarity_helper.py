from ..schemas.webhook_schema import WebhookEventEnum, WebhookSendParams, WebhookEventParams
from ..services.project_variables_service import ProjectVariableService
from ..services.project_config_service import ProjectConfigService
from ..services.webhook_service import WebhookService
from ..rabbitmq.producer import GMQWebhookProducer
from ..services.chunk_service import ChunkService
from ..qdrant.similarity import QdrantSimilarity
from ..libs.embedding_lib import EmbeddingLib
from ..schemas import processor_schema as ps
from app.constants.neo4j import GNeo4jEdges
from ..schemas import chunk_schema as cs
from ..neo4j.chunk import GN4jChunk
from app.utils.logger import logger


class VectorSimilarityHelper:
    # def __init__(self, org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
    @staticmethod
    async def add_edges(cp: ps.CommonParams):
        webhooks = await WebhookService(cp.org_id, cp.project_id).list()
        try:
            logger.info({"message": "Creating vector similarity edges", "document_id": cp.doc_id, "org_id": cp.org_id, "project_id": cp.project_id})

            project_config = await ProjectConfigService(cp.org_id, cp.project_id).get_with_details_by_project()
            project_variables = await ProjectVariableService(cp.org_id, cp.project_id).get_by_project()

            if project_variables is None:
                logger.error({"message": "Project variables not found", "org_id": cp.org_id, "project_id": cp.project_id})
                raise Exception("Project variables not found")
            if project_config is None:
                logger.error({"message": "Project config not found", "org_id": cp.org_id, "project_id": cp.project_id})
                raise Exception("Project config not found")

            embedding_model = project_config.embedding_model

            if embedding_model is None:
                logger.error({"message": "Embedding Model is not configured", "org_id": cp.org_id, "project_id": cp.project_id})
                raise Exception("Embedding Model is not configured")

            ep_model_key = EmbeddingLib.get_model_key(embedding_model.provider.value, embedding_model.dimension)

            list_chunk_id_numbers = await ChunkService(cp.org_id, cp.project_id, cp.doc_id).get_all_chunk_id_and_number()
            chunk_ids = [chunk_id for chunk_id, _ in list_chunk_id_numbers]
            qdrant_similarity = QdrantSimilarity(cp.org_id, cp.project_id)

            result: dict[str, list[cs.ChunkDenseVectorScore]] = await qdrant_similarity.get_similar_chunks(model_key=ep_model_key, document_id=cp.doc_id, chunk_ids=chunk_ids, top_k=project_variables.gte_edge_vector_similar_top_k, limit=project_variables.max_chunks, threshold=project_variables.gte_edge_vector_similar_threshold)

            n4j_similarity_edges: list[cs.N4jChunkEdge] = []

            for from_chunk_id, obj in result.items():
                for chunk_score in obj:
                    n4j_similarity_edges.append(cs.N4jChunkEdge(from_chunk_id=from_chunk_id, to_chunk_id=chunk_score.chunk_id, edge_name=GNeo4jEdges.VECTOR_SIMILARITY, label="vector_similarity", weight=chunk_score.score))

            await GN4jChunk(org_id=cp.org_id, project_id=cp.project_id).create_edges(cp.doc_id, n4j_similarity_edges)

            logger.info({"message": "Created vector similarity edges", "document_id": cp.doc_id, "org_id": cp.org_id, "project_id": cp.project_id})

            await GMQWebhookProducer.publish_to_webhook_exchange(WebhookSendParams(event_data=WebhookEventParams(event=WebhookEventEnum.DOCUMENT_VECTOR_SIMILARITY_PROCESSED, data={"document_id": cp.doc_id, "org_id": cp.org_id, "project_id": cp.project_id}), webhooks=webhooks))
        except Exception as e:
            logger.error({"message": "Failed to add edges", "error": str(e)})
            await GMQWebhookProducer.publish_to_webhook_exchange(WebhookSendParams(event_data=WebhookEventParams(event=WebhookEventEnum.DOCUMENT_VECTOR_SIMILARITY_FAILED, data={"document_id": cp.doc_id, "org_id": cp.org_id, "project_id": cp.project_id}), webhooks=webhooks))
            raise e
