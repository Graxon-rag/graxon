from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class QueryExpansionResponse(BaseModel):
    expanded_query: str = Field(
        description="One conservative retrieval-optimized rewrite of the user query."
    )


QUERY_EXPANSION_SYSTEM_PROMPT = """
You are a retrieval query rewriting assistant.

Rewrite the user's query into ONE search-friendly query for document retrieval.

Rules:
1. Preserve the user's original intent exactly.
2. Preserve names, acronyms, identifiers, numbers, dates, versions, and technical terms.
3. Add only useful synonyms, expansions, or clarifying terms that improve retrieval.
4. Do not answer the question.
5. Do not add facts that are not implied by the query.
6. Keep the rewrite concise: one sentence or keyword-style query.
"""


QUERY_EXPANSION_HUMAN_PROMPT = """
USER QUERY:
{query}

Return only the structured response.
"""


QUERY_EXPANSION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", QUERY_EXPANSION_SYSTEM_PROMPT),
    ("human", QUERY_EXPANSION_HUMAN_PROMPT),
])
