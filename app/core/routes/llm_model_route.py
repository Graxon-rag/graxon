from fastapi import HTTPException, APIRouter, Query, Body
from app.utils.logger import logger
from ..handlers.llm_model_handler import LLMModelHandler
from ..schemas.llm_model_schema import LLMModelCreateSchema
from app.constants.model_provider import LLMModelProvider
from app.utils.response_util import success_response, error_response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
import uuid


router = APIRouter(
    tags=["LLM Model"],
    # dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)


@router.post("/{org_id}/create")
async def create_llm_model(org_id: str, data: LLMModelCreateSchema):
    try:
        handler = LLMModelHandler(org_id=org_id)
        result = await handler.create(data)
        if not result:
            logger.error({"message": "Failed to create LLM model", "result": result})
            return error_response("Failed to create LLM model", HTTP_400_BAD_REQUEST)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to create LLM model", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{org_id}/create-multiple")
async def create_multiple_llm_models(org_id: str, data: list[LLMModelCreateSchema]):
    try:
        handler = LLMModelHandler(org_id=org_id)
        result = await handler.create_multiple(data)
        if not result:
            logger.error({"message": "Failed to create LLM model", "result": result})
            return error_response("Failed to create LLM model", HTTP_400_BAD_REQUEST)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to create LLM model", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/all/provider/{provider}")
async def get_all_llm_models(org_id: str, provider: LLMModelProvider):
    try:
        handler = LLMModelHandler(org_id=org_id)
        result = await handler.get_all_llm_model_by_provider(provider=provider)
        if not result:
            logger.error({"message": "Failed to get LLM models", "result": result})
            return error_response("Failed to get LLM models", HTTP_404_NOT_FOUND)
        result_array = [result.model_dump(mode="json") for result in result]
        return success_response(data={"data": result_array})
    except Exception as e:
        logger.error({"message": "Failed to get LLM models", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/{llm_model_id}")
async def get_llm_model(org_id: str, llm_model_id: uuid.UUID):
    try:
        handler = LLMModelHandler(org_id=org_id)
        result = await handler.get_llm_model(llm_model_id)
        if not result:
            logger.error({"message": "Failed to get LLM model", "result": result})
            return error_response("Failed to get LLM model", HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get LLM model", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{org_id}/delete/{llm_model_id}")
async def delete_llm_model(org_id: str, llm_model_id: uuid.UUID):
    try:
        handler = LLMModelHandler(org_id=org_id)
        result = await handler.delete(llm_model_id)
        if not result:
            logger.error({"message": "Failed to delete LLM model", "result": result})
            return error_response("Failed to delete LLM model", HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to delete LLM model", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
