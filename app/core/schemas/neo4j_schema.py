from pydantic import BaseModel, Field


class LexicalSemanticResult(BaseModel):
    filtered_noise: list[str] = Field(default_factory=list)
    entity_map: dict[str, dict[str, float]] = Field(default_factory=dict)
    concept_map: dict[str, dict[str, float]] = Field(default_factory=dict)
    keyword_map: dict[str, dict[str, float]] = Field(default_factory=dict)
    phrase_map: dict[str, dict[str, float]] = Field(default_factory=dict)
    acronyms: dict[str, dict] = Field(default_factory=dict)
