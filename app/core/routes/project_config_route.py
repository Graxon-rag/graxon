from ..schemas.project_config_schema import ProjectConfigGetSchema, ProjectConfigUpdateSchema
from app.utils.response_util import success_response, error_response
from ..handlers.project_config_handler import ProjectConfigHandler
from fastapi import HTTPException, APIRouter, Query, Body
from app.utils.logger import logger
from starlette import status
import uuid


router = APIRouter(
    tags=["Project Config"],
    # dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)


@router.get("/{org_id}/{project_id}/get/{config_id}", response_model=ProjectConfigGetSchema)
async def get_project_config(org_id: str, project_id: uuid.UUID, config_id: uuid.UUID):
    try:
        handler = ProjectConfigHandler(org_id, project_id)
        result = await handler.get(config_id)
        if not result:
            logger.error({"message": "Failed to get project config", "result": result})
            return error_response("Failed to get project config", status.HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get project config", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{org_id}/{project_id}/update/{config_id}", response_model=ProjectConfigGetSchema)
async def update_project_config(org_id: str, project_id: uuid.UUID, config_id: uuid.UUID, config: ProjectConfigUpdateSchema = Body(...)):
    try:
        handler = ProjectConfigHandler(org_id, project_id)
        result = await handler.update(config_id, config)
        if not result:
            logger.error({"message": "Failed to update project config", "result": result})
            return error_response("Failed to update project config", status.HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to update project config", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{org_id}/{project_id}/delete/{config_id}")
async def delete_project_config(org_id: str, project_id: uuid.UUID, config_id: uuid.UUID):
    try:
        handler = ProjectConfigHandler(org_id, project_id)
        result = await handler.delete(config_id)
        if not result:
            logger.error({"message": "Failed to delete project config", "result": result})
            return error_response("Failed to delete project config", status.HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to delete project config", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
