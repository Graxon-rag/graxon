from ..schemas.document_schema import DocumentUploadSchema, DocumentGetSignedUrlSchema, CompleteMultipartUploadSchema, PresignedUrlRequestSchema
from starlette.status import (HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND)
from fastapi import HTTPException, APIRouter, File, UploadFile, Query, Body
from app.utils.response_util import success_response, error_response
from ..handlers.document_handler import DocumentHandler
from ..libs.document_lib import DocumentLibs
from ..minio.upload import MinioUploadClient
from app.utils.logger import logger
import uuid

router = APIRouter(
    tags=["Documents"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{org_id}/projects/{project_id}/upload/multipart/{document_id}/init/{file_name}")
async def multipart_upload_init(org_id: str, project_id: uuid.UUID, document_id: uuid.UUID, file_name: str):
    try:
        handler = MinioUploadClient(org_id=org_id, project_id=project_id)
        result = await handler.multipart_upload_init(document_id=document_id, filename=file_name)
        if not result:
            logger.error({"message": "Failed to initiate multipart upload", "result": result})
            return error_response("Failed to initiate multipart upload", HTTP_404_NOT_FOUND)

        return success_response(data=result)
    except Exception as e:
        logger.error({"message": "Failed to initiate multipart upload", "error": str(e)})
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{org_id}/projects/{project_id}/upload/multipart/{document_id}/presigned-url")
async def multipart_upload_presigned_url(org_id: str, project_id: uuid.UUID, document_id: uuid.UUID, body: PresignedUrlRequestSchema):
    try:
        handler = MinioUploadClient(org_id=org_id, project_id=project_id)
        result = await handler.get_multipart_presigned_url(
            document_id=document_id,
            upload_id=body.upload_id,
            key=body.key,
            part_number=body.part_number
        )
        if not result:
            logger.error({"message": "Failed to get presigned url", "result": result})
            return error_response("Failed to get presigned url", HTTP_404_NOT_FOUND)

        return success_response(data=result)
    except Exception as e:
        logger.error({"message": "Failed to get presigned url", "error": str(e)})
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{org_id}/projects/{project_id}/upload/multipart/{document_id}/complete")
async def multipart_upload_complete(org_id: str, project_id: uuid.UUID, document_id: uuid.UUID, body: CompleteMultipartUploadSchema):
    try:
        handler = MinioUploadClient(org_id=org_id, project_id=project_id)
        result = await handler.complete_multipart_upload(
            document_id=document_id,
            upload_id=body.upload_id,
            key=body.key,
            file_name=body.file_name,
            parts=body.parts
        )
        if not result:
            logger.error({"message": "Failed to complete multipart upload", "result": result})
            return error_response("Failed to complete multipart upload", HTTP_404_NOT_FOUND)

        return success_response(data=result)
    except Exception as e:
        logger.error({"message": "Failed to complete multipart upload", "error": str(e)})
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{org_id}/projects/{project_id}/upload/{document_id}")
async def upload_document(org_id: str, project_id: uuid.UUID, document_id: uuid.UUID, file: UploadFile = File(...)):
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
            id=document_id,
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


@router.get("/{org_id}/projects/{project_id}/get/all")
async def get_all_documents(org_id: str, project_id: uuid.UUID):
    try:
        handler = DocumentHandler(org_id=org_id, project_id=project_id)
        result = await handler.get_all()
        if not result:
            logger.error({"message": "Failed to get all documents", "result": result})
            return error_response("Failed to get all documents", HTTP_404_NOT_FOUND)
        result_list = [r.model_dump(mode="json") for r in result]
        return success_response(data={"data": result_list})
    except Exception as e:
        logger.error({"message": "Failed to get all documents", "error": str(e)})
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{org_id}/projects/{project_id}/get/{document_id}")
async def get_document(org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
    try:
        handler = DocumentHandler(org_id=org_id, project_id=project_id)
        result = await handler.get(document_id)
        if not result:
            logger.error({"message": "Failed to get document", "result": result})
            return error_response("Failed to get document", HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get document", "error": str(e)})
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{org_id}/projects/{project_id}/delete/{document_id}")
async def delete_document(org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
    try:
        handler = DocumentHandler(org_id=org_id, project_id=project_id)
        result = await handler.delete(document_id)
        if not result:
            logger.error({"message": "Failed to delete document", "result": result})
            return error_response("Failed to delete document", HTTP_404_NOT_FOUND)
        return success_response(data={"success": True})
    except Exception as e:
        logger.error({"message": "Failed to delete document", "error": str(e)})
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


@router.post("/{org_id}/projects/{project_id}/process/{document_id}")
async def submit_process_document(org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
    try:
        handler = DocumentHandler(org_id=org_id, project_id=project_id)
        result = await handler.submit_process_document(document_id)

        if not result:
            logger.error({"message": "Failed to process document", "result": result})
            return error_response("Failed to process document", HTTP_404_NOT_FOUND)

        return success_response(data={"Accepted": True}, message="Accepted", status_code=202)
    except Exception as e:
        logger.error({"message": "Failed to process document", "error": str(e)})
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
