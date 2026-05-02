from fastapi import HTTPException, APIRouter, Query, Body
from app.utils.logger import logger
from ..handlers.reranker_handler import ReRankerHandler
from ..schemas.reranker_schema import ReRankerCreateSchema
from app.utils.response_util import success_response, error_response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
import uuid


router = APIRouter(
    tags=["Reranker"],
    # dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)


@router.post("/{org_id}/create")
async def create_reranker(org_id: str, reranker: ReRankerCreateSchema = Body(...)):
    try:
        handler = ReRankerHandler(org_id=org_id)
        result = await handler.create_reranker(reranker)
        if not result:
            logger.error({"message": "Failed to create reranker", "result": result})
            return error_response("Failed to create reranker", HTTP_400_BAD_REQUEST)
        return success_response(data=result.model_dump(mode="json"))

    except Exception as e:
        logger.error({"message": "Failed to create reranker", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{org_id}/create-multiple")
async def create_multiple_rerankers(org_id: str, rerankers: list[ReRankerCreateSchema] = Body(...)):
    try:
        handler = ReRankerHandler(org_id=org_id)
        result = await handler.create_multiple_rerankers(rerankers)
        if not result:
            logger.error({"message": "Failed to create reranker", "result": result})
            return error_response("Failed to create reranker", HTTP_400_BAD_REQUEST)
        return success_response(data={"success": True})

    except Exception as e:
        logger.error({"message": "Failed to create reranker", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/{reranker_id}")
async def get_reranker(org_id: str, reranker_id: uuid.UUID):
    try:
        handler = ReRankerHandler(org_id=org_id)
        result = await handler.get_reranker(reranker_id)
        if not result:
            logger.error({"message": "Failed to get reranker", "result": result})
            return error_response("Failed to get reranker", HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))

    except Exception as e:
        logger.error({"message": "Failed to get reranker", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/all")
async def get_all_rerankers(org_id: str):
    try:
        handler = ReRankerHandler(org_id=org_id)
        result = await handler.get_all_rerankers()
        if not result:
            logger.error({"message": "Failed to get rerankers", "result": result})
            return error_response("Failed to get rerankers", HTTP_404_NOT_FOUND)
        result_array = [result.model_dump(mode="json") for result in result]
        return success_response(data={"data": result_array})

    except Exception as e:
        logger.error({"message": "Failed to get rerankers", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{org_id}/delete/{reranker_id}")
async def delete_reranker(org_id: str, reranker_id: uuid.UUID):
    try:
        handler = ReRankerHandler(org_id=org_id)
        result = await handler.delete_reranker(reranker_id)
        if not result:
            logger.error({"message": "Failed to delete reranker", "result": result})
            return error_response("Failed to delete reranker", HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})

    except Exception as e:
        logger.error({"message": "Failed to delete reranker", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
