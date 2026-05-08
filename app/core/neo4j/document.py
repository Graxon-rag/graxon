from .interfaces.document_interface import N4jDocumentInterface
from ..databases.neo4j.client import GNeo4jClient
from app.constants.neo4j import GN4jNodes, GNeo4jEdges
from typing import cast, LiteralString
from app.utils.logger import logger
import uuid


class GN4jDocument:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.graph = GNeo4jClient.get_driver()
        self.org_id = org_id
        self.project_id = project_id

    async def create(self, doc_id: uuid.UUID, doc_readable_id: str):
        try:
            query = f"""
                MATCH (og:{GN4jNodes.ORGANIZATION} {{id: $org_id}})-[:{GNeo4jEdges.HAS_PROJECT}]->(pr:{GN4jNodes.PROJECT} {{id: $project_id}})
                WITH pr
                MERGE (dc:{GN4jNodes.DOCUMENT} {{id: $doc_id}})
                SET
                    dc.{N4jDocumentInterface.org_id} = $org_id,
                    dc.{N4jDocumentInterface.project_id} = $project_id,
                    dc.{N4jDocumentInterface.id} = $doc_id,
                    dc.{N4jDocumentInterface.readable_id} = $doc_readable_id,
                    dc.{N4jDocumentInterface.created_at} = datetime(),
                    dc.{N4jDocumentInterface.updated_at} = datetime()
                MERGE (pr)-[:{GNeo4jEdges.HAS_DOCUMENT}]->(dc)
            """
            query = cast(LiteralString, query)
            await self.graph.execute_query(
                query,
                {
                    "org_id": self.org_id,
                    "project_id": str(self.project_id),
                    "doc_id": str(doc_id),
                    "doc_readable_id": doc_readable_id
                }
            )

        except Exception as e:
            logger.error({"message": "Failed to create document", "error": str(e)})
            raise e

    async def get(self, document_id: uuid.UUID):
        try:
            query = f"""
                MATCH (og:{GN4jNodes.ORGANIZATION} {{id: $org_id}})-[:{GNeo4jEdges.HAS_PROJECT}]->(pr:{GN4jNodes.PROJECT} {{id: $project_id}})
                MATCH (pr)-[:{GNeo4jEdges.HAS_DOCUMENT}]->(dc:{GN4jNodes.DOCUMENT} {{id: $doc_id}})
                RETURN dc
            """
            query = cast(LiteralString, query)
            return await self.graph.execute_query(query, {"org_id": self.org_id, "project_id": str(self.project_id), "doc_id": str(document_id)})
        except Exception as e:
            logger.error({"message": "Failed to get document", "error": str(e)})
            raise e

    async def delete(self, document_id: uuid.UUID):
        try:
            query = f"""
                MATCH (og:{GN4jNodes.ORGANIZATION} {{id: $org_id}})-[:{GNeo4jEdges.HAS_PROJECT}]->(pr:{GN4jNodes.PROJECT} {{id: $project_id}})
                MATCH (pr)-[:{GNeo4jEdges.HAS_DOCUMENT}]->(dc:{GN4jNodes.DOCUMENT} {{id: $doc_id}})
                DETACH DELETE dc
            """
            query = cast(LiteralString, query)
            return await self.graph.execute_query(query, {"org_id": self.org_id, "project_id": str(self.project_id), "doc_id": str(document_id)})
        except Exception as e:
            logger.error({"message": "Failed to delete document", "error": str(e)})
            raise e
