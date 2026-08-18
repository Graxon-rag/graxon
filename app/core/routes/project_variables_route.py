from ..helpers.project_variables import PROJECT_VARIABLES_DEFAULT_VALUES
from ..handlers.project_variables_handler import ProjectVariableHandler
from app.utils.response_util import success_response, error_response
from fastapi import HTTPException, APIRouter
from app.utils.logger import logger
from starlette import status
import uuid


router = APIRouter(
    tags=["Project Variables"],
    responses={404: {"description": "Not found"}},
)


@router.get("/default")
async def get_default_project_variables():
    try:
        return success_response({"data": PROJECT_VARIABLES_DEFAULT_VALUES}, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")


@router.get("/{org_id}/{project_id}")
async def get_project_variables(org_id: str, project_id: uuid.UUID):
    try:
        handler = ProjectVariableHandler(org_id, project_id)
        result = await handler.get_by_project()
        if not result:
            logger.error({"message": "Failed to get project variables", "result": result})
            return error_response("Failed to get project variables", status.HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get project variables", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
