from app.utils.response_util import success_response, error_response
from ..schemas.video_model_schema import VideoModelCreateSchema
from ..handlers.video_model_handler import VideoModelHandler
from app.constants.model_provider import VideoModelProvider
from fastapi import HTTPException, APIRouter, Query, Body
from app.utils.logger import logger
from starlette import status
import uuid


router = APIRouter(
    tags=["Video Model"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{org_id}/create")
async def create_video_model(org_id: str, video_model: VideoModelCreateSchema = Body(...)):
    try:
        result = await VideoModelHandler(org_id).create(video_model)
        if not result:
            logger.error({"message": "Failed to create video model", "result": result})
            return error_response("Failed to create video model", status.HTTP_400_BAD_REQUEST)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{org_id}/create-multiple")
async def create_multiple_video_models(org_id: str, video_models: list[VideoModelCreateSchema] = Body(...)):
    try:
        result = await VideoModelHandler(org_id).create_multiple(video_models)
        if not result:
            logger.error({"message": "Failed to create video model", "result": result})
            return error_response("Failed to create video model", status.HTTP_400_BAD_REQUEST)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/{video_model_id}")
async def get_video_model(org_id: str, video_model_id: uuid.UUID):
    try:
        handler = VideoModelHandler(org_id=org_id)
        result = await handler.get(video_model_id)
        if not result:
            logger.error({"message": "Failed to get video model", "result": result})
            return error_response("Failed to get video model", status.HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get video model", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/all/provider/{provider}")
async def get_all_video_models(org_id: str, provider: VideoModelProvider):
    try:
        handler = VideoModelHandler(org_id=org_id)
        result = await handler.get_by_provider(provider=provider)
        if not result:
            logger.error({"message": "Failed to get video models", "result": result})
            return error_response("Failed to get video models", status.HTTP_404_NOT_FOUND)
        result_array = [result.model_dump(mode="json") for result in result]
        return success_response(data={"data": result_array})
    except Exception as e:
        logger.error({"message": "Failed to get video models", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{org_id}/delete/{video_model_id}")
async def delete_video_model(org_id: str, video_model_id: uuid.UUID):
    try:
        handler = VideoModelHandler(org_id=org_id)
        result = await handler.delete(video_model_id)
        if not result:
            logger.error({"message": "Failed to delete video model", "result": result})
            return error_response("Failed to delete video model", status.HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to delete video model", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
