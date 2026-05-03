from ..schemas.project_schema import ProjectDetailSchema, ProjectGetSchema, ProjectDetailMetadata
from ..services.embedding_model_service import EmbeddingModelService
from ..services.llm_model_service import LLMModelService
from ..services.reranker_service import ReRankerService
from ..services.model_credential_service import ModelCredentialService
from ..services.sparse_text_model_service import SparseTextModelService
from app.utils.logger import logger


class ProjectHelper:
    def __init__(self, org_id):
        self.org_id = org_id

    async def get_project_details(self, project: ProjectGetSchema) -> ProjectDetailSchema:
        try:
            llm_model_id = project.llm_model_id
            embedding_model_id = project.embedding_model_id
            sparse_text_model_id = project.sparse_text_model_id
            reranker_model_id = project.reranker_model_id
            llm_model_credential_id = project.llm_model_credential_id
            embedding_model_credential_id = project.embedding_model_credential_id

            llm_model_service = LLMModelService(self.org_id)
            embedding_model_service = EmbeddingModelService(self.org_id)
            sparse_text_model_service = SparseTextModelService(self.org_id)
            reranker_service = ReRankerService(self.org_id)
            model_credential_service = ModelCredentialService(self.org_id)

            llm_model = await llm_model_service.get_llm_model(llm_model_id)
            embedding_model = await embedding_model_service.get_embedding_model(embedding_model_id)
            sparse_text_model = await sparse_text_model_service.get_sparse_text_model(sparse_text_model_id)
            reranker = await reranker_service.get_reranker(reranker_model_id)
            llm_model_credential = await model_credential_service.get_model_credential(llm_model_credential_id)
            embedding_model_credential = await model_credential_service.get_model_credential(embedding_model_credential_id)

            return ProjectDetailSchema(
                name=project.name,
                description=project.description,
                id=project.id,
                readable_id=project.readable_id,
                org_id=project.org_id,
                details=ProjectDetailMetadata(
                    llm_model=llm_model,
                    embedding_model=embedding_model,
                    sparse_text_model=sparse_text_model,
                    reranker=reranker,
                    llm_model_credential=llm_model_credential,
                    embedding_model_credential=embedding_model_credential
                )
            )
        except Exception as e:
            logger.error({"message": "Failed to get project details", "error": str(e)})
            raise e
