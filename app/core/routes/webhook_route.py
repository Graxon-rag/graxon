from app.utils.response_util import success_response, error_response
from ..schemas.webhook_schema import WebhookCreateSchema
from ..handlers.webhook_handler import WebhookHandler
from fastapi import HTTPException, APIRouter, Body
from app.utils.logger import logger
from starlette import status
import uuid

router = APIRouter(
    tags=["Webhooks"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{org_id}/{project_id}/create")
async def create_webhook(org_id: str, project_id: str, webhook: WebhookCreateSchema = Body(...)):
    try:
        result = await WebhookHandler(org_id, uuid.UUID(project_id)).create(webhook)
        if not result:
            logger.error({"message": "Failed to create webhook", "result": result})
            return error_response("Failed to create webhook", status.HTTP_400_BAD_REQUEST)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/{project_id}/get/{webhook_id}")
async def get_webhook(org_id: str, project_id: str, webhook_id: uuid.UUID):
    try:
        handler = WebhookHandler(org_id=org_id, project_id=uuid.UUID(project_id))
        result = await handler.get(webhook_id)
        if not result:
            logger.error({"message": "Failed to get webhook", "result": result})
            return error_response("Failed to get webhook", status.HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get webhook", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/{project_id}/list")
async def list_webhooks(org_id: str, project_id: str):
    try:
        handler = WebhookHandler(org_id=org_id, project_id=uuid.UUID(project_id))
        result = await handler.list()
        if not result:
            logger.error({"message": "Failed to get webhooks", "result": result})
            return error_response("Failed to get webhooks", status.HTTP_404_NOT_FOUND)
        result_array = [result.model_dump(mode="json") for result in result]
        return success_response(data={"data": result_array})
    except Exception as e:
        logger.error({"message": "Failed to get webhooks", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{org_id}/{project_id}/delete/{webhook_id}")
async def delete_webhook(org_id: str, project_id: str, webhook_id: uuid.UUID):
    try:
        handler = WebhookHandler(org_id=org_id, project_id=uuid.UUID(project_id))
        result = await handler.delete(webhook_id)
        if not result:
            logger.error({"message": "Failed to delete webhook", "result": result})
            return error_response("Failed to delete webhook", status.HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to delete webhook", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
