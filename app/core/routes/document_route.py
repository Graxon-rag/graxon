from fastapi import HTTPException, APIRouter, File, UploadFile, Query
from ..handlers.document_handler import DocumentHandler
from starlette.status import (HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST)
from app.utils.logger import logger
from app.utils.response_util import success_response, error_response
from ..schemas.document_schema import DocumentUploadSchema, DocumentGetSignedUrlSchema
from ..libs.document_lib import DocumentLibs
import uuid

router = APIRouter(
    tags=["Documents"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{org_id}/projects/{project_id}/upload")
async def upload_document(org_id: str, project_id: uuid.UUID, file: UploadFile = File(...)):
    try:
        filename = file.filename
        if not filename:
            return error_response("File name is required", HTTP_400_BAD_REQUEST)

        if not DocumentLibs.allowed_file(filename):
            return error_response(
                "Only .txt, .pdf, and .md files are allowed",
                HTTP_400_BAD_REQUEST
            )

        file_type = file.content_type
        if not file_type:
            return error_response("File type is required", HTTP_400_BAD_REQUEST)

        doc = DocumentUploadSchema(
            org_id=org_id,
            project_id=project_id,
            name=filename,
            type=file_type
        )

        handler = DocumentHandler(org_id=org_id, project_id=project_id)
        result = await handler.handle_document_upload(doc, file)
        if not result:
            logger.error({"message": "Failed to upload document", "result": result})
            return error_response("Failed to upload document", HTTP_400_BAD_REQUEST)
        return success_response(data=result.model_dump(mode="json"))

    except Exception as e:
        logger.error({
            "message": "Failed to upload document",
            "error": str(e)
        })
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{org_id}/projects/{project_id}/get-signed-url")
async def get_document_signed_url(org_id: str, project_id: uuid.UUID, bucket: str = Query(..., description="S3/MinIO bucket name"), key: str = Query(..., description="Object key (path inside bucket)")):
    try:
        document = DocumentGetSignedUrlSchema(
            org_id=org_id,
            project_id=project_id,
            bucket=bucket,
            key=key
        )
        handler = DocumentHandler(org_id=org_id, project_id=project_id)
        return await handler.get_document_signed_url(document)
    except Exception as e:
        logger.error({"message": "Failed to get document signed url", "error": str(e)})
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
