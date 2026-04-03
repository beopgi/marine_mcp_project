"""FastAPI route handlers exposing each architecture stage."""

from fastapi import APIRouter, HTTPException

from app.schemas.content import MCPSearchRequest, MCPSearchResponse
from app.schemas.query import QueryStructureResponse, UserQueryRequest
from app.schemas.recommendation import (
    PipelineRunResponse,
    RecommendRequest,
    RecommendResponse,
    RecommendationResult,
)
from app.services.pipeline import build_agent

router = APIRouter()
agent = build_agent()


@router.get('/health')
def health() -> dict:
    """Health-check endpoint."""

    return {'status': 'ok'}


@router.post('/query/structure', response_model=QueryStructureResponse)
def structure_query(request: UserQueryRequest) -> QueryStructureResponse:
    """Natural language -> structured query."""

    structured = agent.structure_query(request.user_input)
    return QueryStructureResponse(structured_query=structured)


@router.post('/mcp/search', response_model=MCPSearchResponse)
def mcp_search(request: MCPSearchRequest) -> MCPSearchResponse:
    """Structured query -> candidate pool via MCP."""

    trace_id, candidates = agent.search_candidates(request.structured_query)
    return MCPSearchResponse(candidates=candidates, trace_id=trace_id)


@router.post('/recommend', response_model=RecommendResponse)
def recommend(request: RecommendRequest) -> RecommendResponse:
    """Recommendation from supplied query+candidates or user_input-triggered structuring."""

    if request.structured_query is None:
        if not request.user_input:
            raise HTTPException(status_code=400, detail='user_input 또는 structured_query가 필요합니다.')
        structured = agent.structure_query(request.user_input)
    else:
        structured = request.structured_query

    user_input = request.user_input or ''
    recommendation = agent.recommend(user_input, structured, request.candidates)
    return RecommendResponse(recommendation=recommendation)


@router.post('/pipeline/run', response_model=RecommendationResult)
def run_pipeline(request: UserQueryRequest) -> RecommendationResult:
    """Run full architecture pipeline end-to-end and return final recommendation only."""

    result = agent.run_pipeline(request.user_input)
    return result.final_recommendation