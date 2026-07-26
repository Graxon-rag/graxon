from app.utils.response_util import success_response, error_response
from ..schemas.ocr_model_schema import OCRModelCreateSchema
from app.constants.model_provider import OCRModelProvider
from fastapi import HTTPException, APIRouter, Query, Body
from ..handlers.ocr_model_handler import OCRModelHandler
from app.utils.logger import logger
from starlette import status
import uuid


router = APIRouter(
    tags=["OCR Model"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{org_id}/create")
async def create_ocr_model(org_id: str, ocr_model: OCRModelCreateSchema = Body(...)):
    try:
        result = await OCRModelHandler(org_id).create(ocr_model)
        if not result:
            logger.error({"message": "Failed to create OCR model", "result": result})
            return error_response("Failed to create OCR model", status.HTTP_400_BAD_REQUEST)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{org_id}/create-multiple")
async def create_multiple_ocr_models(org_id: str, ocr_models: list[OCRModelCreateSchema] = Body(...)):
    try:
        result = await OCRModelHandler(org_id).create_multiple(ocr_models)
        if not result:
            logger.error({"message": "Failed to create OCR model", "result": result})
            return error_response("Failed to create OCR model", status.HTTP_400_BAD_REQUEST)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/all/provider/{provider}")
async def get_all_ocr_models(org_id: str, provider: OCRModelProvider):
    try:
        handler = OCRModelHandler(org_id=org_id)
        result = await handler.get_by_provider(provider=provider)
        if not result:
            logger.error({"message": "Failed to get OCR models", "result": result})
            return error_response("Failed to get OCR models", status.HTTP_404_NOT_FOUND)
        result_array = [result.model_dump(mode="json") for result in result]
        return success_response(data={"data": result_array})
    except Exception as e:
        logger.error({"message": "Failed to get OCR models", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/{ocr_model_id}")
async def get_ocr_model(org_id: str, ocr_model_id: uuid.UUID):
    try:
        handler = OCRModelHandler(org_id=org_id)
        result = await handler.get(ocr_model_id)
        if not result:
            logger.error({"message": "Failed to get OCR model", "result": result})
            return error_response("Failed to get OCR model", status.HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get OCR model", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{org_id}/delete/{ocr_model_id}")
async def delete_ocr_model(org_id: str, ocr_model_id: uuid.UUID):
    try:
        handler = OCRModelHandler(org_id=org_id)
        result = await handler.delete(ocr_model_id)
        if not result:
            logger.error({"message": "Failed to delete OCR model", "result": result})
            return error_response("Failed to delete OCR model", status.HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to delete OCR model", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
