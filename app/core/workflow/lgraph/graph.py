from .document_ingest_graph import DocumentIngestGraph, DIGState
from app.utils.logger import logger
from app.core.schemas.document_schema import DocumentGetSchema
from ..schemas.provider_schema import ProviderSchema
import uuid


class Graph:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id

    async def ingest_document(self, document: DocumentGetSchema, providers: ProviderSchema):
        try:
            print("Document:", document.model_dump(mode="json"))
            print("Providers:", providers.model_dump(mode="json"))

            request_id = str(uuid.uuid4())
            graph = DocumentIngestGraph(org_id=self.org_id, project_id=self.project_id, document_id=document.id)
            workflow = graph.build_graph()
            initial_state: DIGState = {
                "request_id": request_id,
                "org_id": self.org_id,
                "project_id": self.project_id,
                "document_id": document.id,
                "document": document,
                "providers": providers,
                "temp_path": None
            }
            if workflow is None:
                raise Exception("Workflow is None")

            temp_path = None

            try:
                result = await workflow.ainvoke(initial_state)
                temp_path = result.get("temp_path")
                return result
            except Exception as e:
                logger.error({"message": "Failed to ingest document", "error": str(e)})
                raise e
            finally:
                # Delete temp folder
                import shutil
                if temp_path:
                    shutil.rmtree(temp_path, ignore_errors=True)
                    logger.info({"message": "Deleted temp folder", "path": temp_path})

        except Exception as e:
            logger.error({"message": "Failed to ingest document", "error": str(e)})
            raise e
