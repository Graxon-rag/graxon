from fastapi import HTTPException, APIRouter, Query, Body
from app.utils.logger import logger
from ..handlers.org_handler import OrgHandler
from ..schemas.org_schema import OrgCreateSchema
from app.utils.response_util import success_response, error_response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
import uuid


router = APIRouter(
    tags=["Organization"],
    # dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)


@router.post("/create")
async def create_org(data: OrgCreateSchema = Body(...)):
    try:
        handler = OrgHandler()
        result = await handler.create(data)
        if not result:
            logger.error({"message": "Failed to create organization", "result": result})
            return error_response("Failed to create organization", HTTP_400_BAD_REQUEST)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to create organization", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/get/all")
async def get_all_orgs():
    try:
        handler = OrgHandler()
        result = await handler.get_all()
        if not result:
            logger.error({"message": "Failed to get organizations", "result": result})
            return error_response("Failed to get organizations", HTTP_404_NOT_FOUND)
        result_array = [result.model_dump(mode="json") for result in result]
        return success_response(data={"data": result_array})
    except Exception as e:
        logger.error({"message": "Failed to get organizations", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/get/{org_id}")
async def get_org(org_id: str):
    try:
        handler = OrgHandler()
        result = await handler.get(org_id)
        if not result:
            logger.error({"message": "Failed to get organization", "result": result})
            return error_response("Failed to get organization", HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get organization", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/delete/{org_id}")
async def delete_org(org_id: str):
    try:
        handler = OrgHandler()
        result = await handler.delete(org_id)
        if not result:
            logger.error({"message": "Failed to delete organization", "result": result})
            return error_response("Failed to delete organization", HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to delete organization", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
