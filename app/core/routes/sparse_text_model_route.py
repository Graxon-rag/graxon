from fastapi import HTTPException, APIRouter, Query, Body
from app.utils.logger import logger
from ..handlers.sparse_text_model_handler import SparseTextModelHandler
from ..schemas.sparse_text_model_schema import SparseTextModelCreateSchema
from app.utils.response_util import success_response, error_response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
import uuid


router = APIRouter(
    tags=["SparseTextModel"],
    # dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)


@router.post("/{org_id}/create")
async def create_sparse_text_model(org_id: str, sparse_text_model: SparseTextModelCreateSchema = Body(...)):
    try:
        handler = SparseTextModelHandler(org_id=org_id)
        result = await handler.create_sparse_text_model(sparse_text_model)
        if not result:
            logger.error({"message": "Failed to create sparse text model", "result": result})
            return error_response("Failed to create sparse text model", HTTP_400_BAD_REQUEST)
        return success_response(data=result.model_dump(mode="json"))

    except Exception as e:
        logger.error({"message": "Failed to create sparse text model", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{org_id}/create-multiple")
async def create_multiple_sparse_text_models(org_id: str, sparse_text_models: list[SparseTextModelCreateSchema] = Body(...)):
    try:
        handler = SparseTextModelHandler(org_id=org_id)
        result = await handler.create_multiple_sparse_text_models(sparse_text_models)
        if not result:
            logger.error({"message": "Failed to create sparse text model", "result": result})
            return error_response("Failed to create sparse text model", HTTP_400_BAD_REQUEST)
        return success_response(data={"success": True})

    except Exception as e:
        logger.error({"message": "Failed to create sparse text model", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/{sparse_text_model_id}")
async def get_sparse_text_model(org_id: str, sparse_text_model_id: uuid.UUID):
    try:
        handler = SparseTextModelHandler(org_id=org_id)
        result = await handler.get_sparse_text_model(sparse_text_model_id)
        if not result:
            logger.error({"message": "Failed to get sparse text model", "result": result})
            return error_response("Failed to get sparse text model", HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))

    except Exception as e:
        logger.error({"message": "Failed to get sparse text model", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/all")
async def get_all_sparse_text_models(org_id: str):
    try:
        handler = SparseTextModelHandler(org_id=org_id)
        result = await handler.get_all_sparse_text_models()
        if not result:
            logger.error({"message": "Failed to get sparse text models", "result": result})
            return error_response("Failed to get sparse text models", HTTP_404_NOT_FOUND)
        result_array = [result.model_dump(mode="json") for result in result]
        return success_response(data={"data": result_array})

    except Exception as e:
        logger.error({"message": "Failed to get sparse text models", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{org_id}/delete/{sparse_text_model_id}")
async def delete_sparse_text_model(org_id: str, sparse_text_model_id: uuid.UUID):
    try:
        handler = SparseTextModelHandler(org_id=org_id)
        result = await handler.delete_sparse_text_model(sparse_text_model_id)
        if not result:
            logger.error({"message": "Failed to delete sparse text model", "result": result})
            return error_response("Failed to delete sparse text model", HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})

    except Exception as e:
        logger.error({"message": "Failed to delete sparse text model", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
