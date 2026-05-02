from fastapi import HTTPException, APIRouter, Query, Body
from app.utils.logger import logger
from ..handlers.model_credential_handler import ModelCredentialHandler
from ..schemas.model_credential_schema import ModelCredentialCreateSchema
from app.constants.model_provider import ModelProvider
from app.utils.response_util import success_response, error_response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
import uuid


router = APIRouter(
    tags=["Model Credential"],
    # dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)


@router.post("/{org_id}/create")
async def create_model_credential(org_id: str, model_credential: ModelCredentialCreateSchema = Body(...)):
    try:
        handler = ModelCredentialHandler(org_id=org_id)
        result = await handler.create_model_credential(model_credential)
        if not result:
            logger.error({"message": "Failed to create model credential", "result": result})
            return error_response("Failed to create model credential", HTTP_400_BAD_REQUEST)
        return success_response(data=result.model_dump(mode="json"))

    except Exception as e:
        logger.error({"message": "Failed to create model credential", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/all/provider/{provider}")
async def get_all_model_credentials(org_id: str, provider: ModelProvider):
    try:
        handler = ModelCredentialHandler(org_id=org_id)
        result = await handler.get_all_model_credentials(provider=provider)
        if not result:
            logger.error({"message": "Failed to get model credentials", "result": result})
            return error_response("Failed to get model credentials", HTTP_404_NOT_FOUND)
        result_array = [result.model_dump(mode="json") for result in result]
        return success_response(data={"data": result_array})

    except Exception as e:
        logger.error({"message": "Failed to get model credentials", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/{model_credential_id}")
async def get_model_credential(org_id: str, model_credential_id: uuid.UUID):
    try:
        handler = ModelCredentialHandler(org_id=org_id)
        result = await handler.get_model_credential(model_credential_id)
        if not result:
            logger.error({"message": "Failed to get model credential", "result": result})
            return error_response("Failed to get model credential", HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get model credential", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{org_id}/delete/{model_credential_id}")
async def delete_model_credential(org_id: str, model_credential_id: uuid.UUID):
    try:
        handler = ModelCredentialHandler(org_id=org_id)
        result = await handler.delete_model_credential(model_credential_id)
        if not result:
            logger.error({"message": "Failed to delete model credential", "result": result})
            return error_response("Failed to delete model credential", HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to delete model credential", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
