from ..schemas.project_config_schema import ProjectConfigDetailGetSchema, ProjectConfigGetSchema
from ..services.sparse_text_model_service import SparseTextModelService
from ..services.model_credential_service import ModelCredentialService
from ..services.embedding_model_service import EmbeddingModelService
from ..services.audio_model_service import AudioModelService
from ..services.video_model_service import VideoModelService
from ..services.llm_model_service import LLMModelService
from ..services.ocr_model_service import OCRModelService
from ..services.reranker_service import ReRankerService
from app.utils.logger import logger
import uuid


class ProjectHelper:
    def __init__(self, org_id):
        self.org_id = org_id

    # async def get_project_details(self, project: ProjectGetSchema) -> ProjectDetailSchema:
    #     try:
    #         llm_model_id = project.llm_model_id
    #         embedding_model_id = project.embedding_model_id
    #         sparse_text_model_id = project.sparse_text_model_id
    #         reranker_model_id = project.reranker_model_id
    #         llm_model_credential_id = project.llm_model_credential_id
    #         embedding_model_credential_id = project.embedding_model_credential_id

    #         llm_model_service = LLMModelService(self.org_id)
    #         embedding_model_service = EmbeddingModelService(self.org_id)
    #         sparse_text_model_service = SparseTextModelService(self.org_id)
    #         reranker_service = ReRankerService(self.org_id)
    #         model_credential_service = ModelCredentialService(self.org_id)

    #         llm_model = await llm_model_service.get_llm_model(llm_model_id)
    #         embedding_model = await embedding_model_service.get_embedding_model(embedding_model_id)
    #         sparse_text_model = await sparse_text_model_service.get_sparse_text_model(sparse_text_model_id)
    #         reranker = await reranker_service.get_reranker(reranker_model_id)
    #         llm_model_credential = await model_credential_service.get_model_credential(llm_model_credential_id)
    #         embedding_model_credential = await model_credential_service.get_model_credential(embedding_model_credential_id)

    #         return ProjectDetailSchema(
    #             name=project.name,
    #             description=project.description,
    #             id=project.id,
    #             readable_id=project.readable_id,
    #             org_id=project.org_id,
    #             details=ProjectDetailMetadata(
    #                 llm_model=llm_model,
    #                 embedding_model=embedding_model,
    #                 sparse_text_model=sparse_text_model,
    #                 reranker=reranker,
    #                 llm_model_credential=llm_model_credential,
    #                 embedding_model_credential=embedding_model_credential
    #             )
    #         )
    #     except Exception as e:
    #         logger.error({"message": "Failed to get project details", "error": str(e)})
    #         raise e


class ProjectConfigHelper:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id

    async def get_project_config_detail(self, pc: ProjectConfigGetSchema) -> ProjectConfigDetailGetSchema:
        try:
            pcd: ProjectConfigDetailGetSchema = ProjectConfigDetailGetSchema(id=pc.id, project_id=pc.project_id, graph_db_enable=pc.graph_db_enable, sparse_embedding_enable=pc.sparse_embedding_enable, llm_tag_extraction_enable=pc.llm_tag_extraction_enable, reranker_enable=pc.reranker_enable, created_at=pc.created_at, updated_at=pc.updated_at)

            llm_model_id = pc.llm_model_id
            embedding_model_id = pc.embedding_model_id

            if llm_model_id:
                llm_model_service = LLMModelService(self.org_id)
                llm_model = await llm_model_service.get_llm_model(llm_model_id)
                llm_model_credential_service = ModelCredentialService(self.org_id)
                llm_model_credential = await llm_model_credential_service.get_model_credential(pc.llm_model_credential_id)

                pcd.llm_model = llm_model
                pcd.llm_model_credential = llm_model_credential

            if embedding_model_id:
                embedding_model_service = EmbeddingModelService(self.org_id)
                embedding_model = await embedding_model_service.get_embedding_model(embedding_model_id)
                embedding_model_credential_service = ModelCredentialService(self.org_id)
                embedding_model_credential = await embedding_model_credential_service.get_model_credential(pc.embedding_model_credential_id)

                pcd.embedding_model = embedding_model
                pcd.embedding_model_credential = embedding_model_credential

            if pc.sparse_embedding_enable and pc.sparse_text_model_id:
                sparse_text_model_service = SparseTextModelService(self.org_id)
                sparse_text_model = await sparse_text_model_service.get(pc.sparse_text_model_id)
                pcd.sparse_text_model = sparse_text_model

                if pc.sparse_text_model_credential_id:
                    sparse_text_model_credential_service = ModelCredentialService(self.org_id)
                    sparse_text_model_credential = await sparse_text_model_credential_service.get_model_credential(pc.sparse_text_model_credential_id)
                    pcd.sparse_text_model_credential = sparse_text_model_credential

            if pc.reranker_enable and pc.reranker_model_id:
                reranker_service = ReRankerService(self.org_id)
                reranker = await reranker_service.get_reranker(pc.reranker_model_id)
                pcd.reranker_model = reranker

                if pc.reranker_model_credential_id:
                    reranker_model_credential_service = ModelCredentialService(self.org_id)
                    reranker_model_credential = await reranker_model_credential_service.get_model_credential(pc.reranker_model_credential_id)
                    pcd.reranker_model_credential = reranker_model_credential

            if pc.ocr_model_id:
                ocr_model_service = OCRModelService(self.org_id)
                ocr_model = await ocr_model_service.get(pc.ocr_model_id)
                pcd.ocr_model = ocr_model

                if pc.ocr_model_credential_id:
                    ocr_model_credential_service = ModelCredentialService(self.org_id)
                    ocr_model_credential = await ocr_model_credential_service.get_model_credential(pc.ocr_model_credential_id)
                    pcd.ocr_model_credential = ocr_model_credential

            if pc.audio_model_id:
                audio_model_service = AudioModelService(self.org_id)
                audio_model = await audio_model_service.get(pc.audio_model_id)
                pcd.audio_model = audio_model

                if pc.audio_model_credential_id:
                    audio_model_credential_service = ModelCredentialService(self.org_id)
                    audio_model_credential = await audio_model_credential_service.get_model_credential(pc.audio_model_credential_id)
                    pcd.audio_model_credential = audio_model_credential

            if pc.video_model_id:
                video_model_service = VideoModelService(self.org_id)
                video_model = await video_model_service.get(pc.video_model_id)
                pcd.video_model = video_model

                if pc.video_model_credential_id:
                    video_model_credential_service = ModelCredentialService(self.org_id)
                    video_model_credential = await video_model_credential_service.get_model_credential(pc.video_model_credential_id)
                    pcd.video_model_credential = video_model_credential

            return pcd
        except Exception as e:
            logger.error({"message": "Failed to get project config details", "error": str(e)})
            raise e
