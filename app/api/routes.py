"""FastAPI route handlers exposing each architecture stage."""

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.adapters.kma_adapter import KMAAdapter
from app.repositories.user_location_repo import (
    LocationDependencyError,
    LocationNotFoundError,
    UserLocationRepository,
)
from app.schemas.content import MCPSearchRequest, MCPSearchResponse
from app.schemas.home import HomeDashboardRequest, HomeDashboardResponse
from app.schemas.query import QueryStructureResponse, UserQueryRequest
from app.schemas.recommendation import (
    HomeRecommendationRequest,
    HomeRecommendationResponse,
    PipelineRunResponse,
    RecommendRequest,
    RecommendResponse,
    RecommendationResult,
)
from app.services.home_dashboard_service import HomeDashboardService
from app.services.home_recommendation import HomeRecommendationService
from app.services.location_context_service import LocationContextService
from app.services.weather_service import WeatherService
from app.services.pipeline import build_agent
from app.repositories.user_preference_repo import UserPreferenceRepository

router = APIRouter()
settings = get_settings()
agent = build_agent()
user_preference_repository = UserPreferenceRepository()
home_recommendation_service = HomeRecommendationService(
    agent=agent,
    user_preference_repository=user_preference_repository,
)
home_dashboard_service = HomeDashboardService(
    agent=agent,
    location_context_service=LocationContextService(
        repository=UserLocationRepository(settings=settings),
    ),
    weather_service=WeatherService(adapter=KMAAdapter(settings=settings)),
    user_preference_repository=user_preference_repository,
)


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

@router.post('/api/recommendations/home', response_model=HomeRecommendationResponse)
def recommend_home(request: HomeRecommendationRequest) -> HomeRecommendationResponse:
    """Tag-based home recommendation endpoint for Flutter BANU."""

    return home_recommendation_service.recommend_home(
        user_id=request.user_id,
        location=request.location,
    )


@router.post('/api/home/dashboard', response_model=HomeDashboardResponse)
async def home_dashboard(request: HomeDashboardRequest) -> HomeDashboardResponse:
    """Flutter home dashboard endpoint backed by DB location and optional KMA weather."""

    try:
        return await home_dashboard_service.build_dashboard(request)
    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "no_location_found", "message": str(exc)},
        ) from exc
    except LocationDependencyError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "dependency_error", "message": str(exc)},
        ) from exc
