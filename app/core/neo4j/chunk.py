from app.constants.neo4j import GN4jNodes, GNeo4jEdges
from ..databases.neo4j.client import GNeo4jClient
from .interfaces.chunk_interface import N4jChunkInterface
from ..schemas.chunk_schema import Chunk
from typing import cast, LiteralString
from app.utils.logger import logger
import uuid


class N4jChunk:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.graph = GNeo4jClient.get_driver()
        self.org_id = org_id
        self.project_id = project_id

    async def create_multiple(self, document_id: uuid.UUID, document_readable_id: str, chunks: list[Chunk]):
        try:
            # Convert Pydantic models to a list of dictionaries for Neo4j parameters
            chunk_data = [chunk.model_dump() for chunk in chunks]

            query = cast(LiteralString, f"""
                MATCH (og:{GN4jNodes.ORGANIZATION} {{id: $org_id}})-[:{GNeo4jEdges.HAS_PROJECT}]->(pr:{GN4jNodes.PROJECT} {{id: $project_id}})-[:{GNeo4jEdges.HAS_DOCUMENT}]->(dc:{GN4jNodes.DOCUMENT} {{id: $document_id}})
                WITH dc
                UNWIND $chunks_list AS chunk_item

                MERGE (ch:{GN4jNodes.CHUNK} {{id: chunk_item.chunk_id}})
                SET
                    ch.{N4jChunkInterface.document_id} = $document_id,
                    ch.{N4jChunkInterface.document_readable_id} = $document_readable_id,
                    ch.{N4jChunkInterface.created_at} = datetime(),
                    ch.{N4jChunkInterface.updated_at} = datetime(),
                    ch.{N4jChunkInterface.text} = chunk_item.text,
                    ch.{N4jChunkInterface.page_number} = chunk_item.page_number,
                    ch.{N4jChunkInterface.title} = chunk_item.title,
                    ch.{N4jChunkInterface.source} = chunk_item.source,
                    ch.{N4jChunkInterface.chunk_number} = chunk_item.chunk_number

                MERGE (dc)-[:{GNeo4jEdges.HAS_CHUNK}]->(ch)
                RETURN count(ch) as created_count
            """)

            params = {
                "org_id": self.org_id,
                "project_id": str(self.project_id),
                "document_id": str(document_id),
                "document_readable_id": document_readable_id,
                "chunks_list": chunk_data
            }

            result, _, _ = await self.graph.execute_query(
                query,
                params,
            )
            logger.info(f"Successfully bulk inserted {result[0]['created_count']} chunks.")
            return result[0]['created_count']

        except Exception as e:
            logger.error({"message": "Failed to create chunks", "error": str(e)})
            raise e
