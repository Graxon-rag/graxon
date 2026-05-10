from .interfaces.project_interface import N4jProjectInterface
from app.constants.neo4j import GN4jNodes, GNeo4jEdges
from ..databases.neo4j.client import GNeo4jClient
from typing import cast, LiteralString
from app.utils.logger import logger
import uuid


class GN4Project:
    def __init__(self, org_id: str):
        self.graph = GNeo4jClient.get_driver()
        self.org_id = org_id

    async def create(self, id: uuid.UUID, readable_id: str, name: str, description: str = "Default description"):
        try:
            id_str = str(id)
            query = f"""
                MATCH (og:{GN4jNodes.ORGANIZATION} {{id: $org_id}})
                WITH og
                MERGE (pr:{GN4jNodes.PROJECT} {{id: $id}})
                SET
                    pr.{N4jProjectInterface.readable_id} = $readable_id,
                    pr.{N4jProjectInterface.name} = $name,
                    pr.{N4jProjectInterface.description} = $description,
                    pr.{N4jProjectInterface.type} = $type,
                    pr.{N4jProjectInterface.created_at} = datetime(),
                    pr.{N4jProjectInterface.updated_at} = datetime()
                MERGE (og)-[:{GNeo4jEdges.HAS_PROJECT}]->(pr)
            """
            query = cast(LiteralString, query)
            await self.graph.execute_query(
                query,
                {
                    "org_id": self.org_id,
                    "id": id_str,
                    "readable_id": readable_id,
                    "name": name,
                    "description": description,
                    "type": GN4jNodes.PROJECT
                }
            )
        except Exception as e:
            logger.error({"message": "Failed to create project", "error": str(e)})
            raise e

    async def get(self, project_id: uuid.UUID):
        try:
            project_id_str = str(project_id)
            query = f"""
                MATCH (og:{GN4jNodes.ORGANIZATION} {{id: $org_id}})-[:{GNeo4jEdges.HAS_PROJECT}]->(pr:{GN4jNodes.PROJECT} {{id: $project_id}})
                RETURN pr
            """
            query = cast(LiteralString, query)
            return await self.graph.execute_query(query, {"org_id": self.org_id, "project_id": project_id_str})
        except Exception as e:
            logger.error({"message": "Failed to get project", "error": str(e)})
            raise e

    async def delete(self, project_id: uuid.UUID):
        try:
            project_id_str = str(project_id)
            query = f"""
                MATCH (og:{GN4jNodes.ORGANIZATION} {{id: $org_id}})-[:{GNeo4jEdges.HAS_PROJECT}]->(pr:{GN4jNodes.PROJECT} {{id: $project_id}})
                DETACH DELETE pr
            """
            query = cast(LiteralString, query)
            return await self.graph.execute_query(query, {"org_id": self.org_id, "project_id": project_id_str})
        except Exception as e:
            logger.error({"message": "Failed to delete project", "error": str(e)})
            raise e
