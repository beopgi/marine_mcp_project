"""Schemas for recommendation requests and responses."""

from pydantic import BaseModel, Field

from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery


class RecommendationResult(BaseModel):
    """Single-item recommendation output with explainability."""

    selected_id: str | None
    reason: str
    matched_constraints: list[str]


class RecommendRequest(BaseModel):
    """Recommendation request that supports raw text or pre-structured query."""

    user_input: str | None = None
    structured_query: StructuredQuery | None = None
    candidates: list[MarineContentItem] = Field(default_factory=list)


class RecommendResponse(BaseModel):
    """Recommendation response wrapper."""

    recommendation: RecommendationResult


class PipelineRunResponse(BaseModel):
    """Full pipeline response including all major outputs."""

    structured_query: StructuredQuery
    filtered_candidates: list[MarineContentItem]
    final_recommendation: RecommendationResult
    trace_id: str
