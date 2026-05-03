from fastapi import HTTPException, APIRouter, Query, Body
from app.utils.logger import logger
from ..handlers.project_handler import ProjectHandler
from ..schemas.project_schema import ProjectCreateSchema
from app.utils.response_util import success_response, error_response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
import uuid


router = APIRouter(
    tags=["Project"],
    # dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)


@router.post("/{org_id}/create")
async def create_project(org_id: str, project: ProjectCreateSchema = Body(...)):
    try:
        handler = ProjectHandler(org_id=org_id)
        result = await handler.create(project)
        if not result:
            logger.error({"message": "Failed to create project", "result": result})
            return error_response("Failed to create project", HTTP_400_BAD_REQUEST)
        return success_response(data=result.model_dump(mode="json"))

    except Exception as e:
        logger.error({"message": "Failed to create project", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/all")
async def get_all_projects(org_id: str):
    try:
        handler = ProjectHandler(org_id=org_id)
        result = await handler.get_all()
        if not result:
            logger.error({"message": "Failed to get projects", "result": result})
            return error_response("Failed to get projects", HTTP_404_NOT_FOUND)
        result_array = [result.model_dump(mode="json") for result in result]
        return success_response(data={"data": result_array})
    except Exception as e:
        logger.error({"message": "Failed to get projects", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{org_id}/get/{project_id}")
async def get_project(org_id: str, project_id: uuid.UUID):
    try:
        handler = ProjectHandler(org_id=org_id)
        result = await handler.get(project_id)
        if not result:
            logger.error({"message": "Failed to get project", "result": result})
            return error_response("Failed to get project", HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get project", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{org_id}/delete/{project_id}")
async def delete_project(org_id: str, project_id: uuid.UUID):
    try:
        handler = ProjectHandler(org_id=org_id)
        result = await handler.delete(project_id)
        if not result:
            logger.error({"message": "Failed to delete project", "result": result})
            return error_response("Failed to delete project", HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to delete project", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
