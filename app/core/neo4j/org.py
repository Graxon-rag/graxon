from .interfaces.org_interface import N4jOrgInterface
from ..databases.neo4j.client import GNeo4jClient
from app.constants.neo4j import GN4jNodes
from typing import cast, LiteralString
from app.utils.logger import logger


class GN4jOrg:
    def __init__(self):
        self.graph = GNeo4jClient.get_driver()

    async def create(
        self,
        org_id: str,
        name: str,
        description: str = "Default description"
    ):
        try:
            query = cast(LiteralString, f"""
                MERGE (og:{GN4jNodes.ORGANIZATION} {{id: $org_id}})
                SET
                    og.{N4jOrgInterface.name} = $name,
                    og.{N4jOrgInterface.description} = $description,
                    og.{N4jOrgInterface.created_at} = datetime(),
                    og.{N4jOrgInterface.updated_at} = datetime()
                """
            )
            await self.graph.execute_query(
                query,
                {
                    "org_id": org_id,
                    "name": name,
                    "description": description
                }
            )

        except Exception as e:
            logger.error({
                "message": "Failed to create org",
                "error": str(e)
            })
            raise e

    async def get(self, org_id: str):
        try:
            query = cast(LiteralString, f"""
                MATCH (og:{GN4jNodes.ORGANIZATION} {{id: $org_id}})
                RETURN og
                """
            )
            result = await self.graph.execute_query(query, {"org_id": org_id})
            return result[0]
        except Exception as e:
            logger.error({
                "message": "Failed to get org",
                "error": str(e)
            })
            raise e

    async def delete(self, org_id: str):
        try:
            query = cast(LiteralString, f"""
                MATCH (og:{GN4jNodes.ORGANIZATION} {{id: $org_id}})
                DETACH DELETE og
                """
            )
            await self.graph.execute_query(query, {"org_id": org_id})
        except Exception as e:
            logger.error({
                "message": "Failed to delete org",
                "error": str(e)
            })
            raise e
