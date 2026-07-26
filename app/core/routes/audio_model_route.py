from app.utils.response_util import success_response, error_response
from ..schemas.audio_model_schema import AudioModelCreateSchema
from ..handlers.audio_model_handler import AudioModelHandler
from app.constants.model_provider import AudioModelProvider
from fastapi import HTTPException, APIRouter, Query, Body
from app.utils.logger import logger
from starlette import status
import uuid


router = APIRouter(
    tags=["Audio/STT Model"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{org_id}/create")
async def create_audio_model(org_id: str, audio_model: AudioModelCreateSchema = Body(...)):
    try:
        result = await AudioModelHandler(org_id).create(audio_model)
        if not result:
            logger.error({"message": "Failed to create audio model", "result": result})
            return error_response("Failed to create audio model", status.HTTP_400_BAD_REQUEST)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{org_id}/create-multiple")
async def create_multiple_audio_models(org_id: str, audio_models: list[AudioModelCreateSchema] = Body(...)):
    try:
        result = await AudioModelHandler(org_id).create_multiple(audio_models)
        if not result:
            logger.error({"message": "Failed to create audio model", "result": result})
            return error_response("Failed to create audio model", status.HTTP_400_BAD_REQUEST)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/{audio_model_id}")
async def get_audio_model(org_id: str, audio_model_id: uuid.UUID):
    try:
        handler = AudioModelHandler(org_id=org_id)
        result = await handler.get(audio_model_id)
        if not result:
            logger.error({"message": "Failed to get audio model", "result": result})
            return error_response("Failed to get audio model", status.HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get audio model", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/all/provider/{provider}")
async def get_all_audio_models(org_id: str, provider: AudioModelProvider):
    try:
        handler = AudioModelHandler(org_id=org_id)
        result = await handler.get_by_provider(provider=provider)
        if not result:
            logger.error({"message": "Failed to get audio models", "result": result})
            return error_response("Failed to get audio models", status.HTTP_404_NOT_FOUND)
        result_array = [result.model_dump(mode="json") for result in result]
        return success_response(data={"data": result_array})
    except Exception as e:
        logger.error({"message": "Failed to get audio models", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{org_id}/delete/{audio_model_id}")
async def delete_audio_model(org_id: str, audio_model_id: uuid.UUID):
    try:
        handler = AudioModelHandler(org_id=org_id)
        result = await handler.delete(audio_model_id)
        if not result:
            logger.error({"message": "Failed to delete audio model", "result": result})
            return error_response("Failed to delete audio model", status.HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to delete audio model", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
