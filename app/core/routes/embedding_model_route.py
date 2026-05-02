from fastapi import HTTPException, APIRouter, Query, Body
from app.utils.logger import logger
from ..handlers.embedding_model_handler import EmbeddingModelHandler
from ..schemas.embedding_model_schema import EmbeddingModelCreateSchema
from app.constants.model_provider import EmbeddingModelProvider
from app.utils.response_util import success_response, error_response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
import uuid


router = APIRouter(
    tags=["Embedding Model"],
    # dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)


@router.post("/{org_id}/create")
async def create_embedding_model(org_id: str, data: EmbeddingModelCreateSchema):
    try:
        handler = EmbeddingModelHandler(org_id=org_id)
        result = await handler.create(data)
        if not result:
            logger.error({"message": "Failed to create embedding model", "result": result})
            return error_response("Failed to create embedding model", HTTP_400_BAD_REQUEST)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to create embedding model", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{org_id}/create-multiple")
async def create_multiple_embedding_models(org_id: str, data: list[EmbeddingModelCreateSchema]):
    try:
        handler = EmbeddingModelHandler(org_id=org_id)
        result = await handler.create_multiple(data)
        if not result:
            logger.error({"message": "Failed to create embedding model", "result": result})
            return error_response("Failed to create embedding model", HTTP_400_BAD_REQUEST)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to create embedding model", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/all/provider/{provider}")
async def get_all_embedding_models(org_id: str, provider: EmbeddingModelProvider):
    try:
        handler = EmbeddingModelHandler(org_id=org_id)
        result = await handler.get_all_embedding_model_by_provider(provider=provider)
        if not result:
            logger.error({"message": "Failed to get embedding models", "result": result})
            return error_response("Failed to get embedding models", HTTP_404_NOT_FOUND)
        result_array = [result.model_dump(mode="json") for result in result]
        return success_response(data={"data": result_array})
    except Exception as e:
        logger.error({"message": "Failed to get embedding models", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/{embedding_model_id}")
async def get_embedding_model(org_id: str, embedding_model_id: uuid.UUID):
    try:
        handler = EmbeddingModelHandler(org_id=org_id)
        result = await handler.get_embedding_model(embedding_model_id)
        if not result:
            logger.error({"message": "Failed to get embedding model", "result": result})
            return error_response("Failed to get embedding model", HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get embedding model", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{org_id}/delete/{embedding_model_id}")
async def delete_embedding_model(org_id: str, embedding_model_id: uuid.UUID):
    try:
        handler = EmbeddingModelHandler(org_id=org_id)
        result = await handler.delete(embedding_model_id)
        if not result:
            logger.error({"message": "Failed to delete embedding model", "result": result})
            return error_response("Failed to delete embedding model", HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to delete embedding model", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
