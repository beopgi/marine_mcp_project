"""Dependency wiring for MCP prototype pipeline."""

from app.adapters.naver_adapter import NaverMarineContentAdapter
from app.agents.llm_agent import LLMAgent
from app.agents.query_structurer import QueryStructurer
from app.agents.recommender import CandidateConstrainedRecommender
from app.core.config import get_settings
from app.llm.gemini_provider import GeminiProvider
from app.mcp.client import MCPClient
from app.mcp.formatter import RequestFormatter
from app.mcp.server import MCPServer
from app.mcp.session import SessionManager
from app.mcp.tool_handler import ToolRequestHandler
from app.repositories.marine_content_repo import MarineContentRepository
from app.services.filtering import FilteringService
from app.services.normalization import NormalizationService
from app.tools.marine_content_query_tool import MarineContentQueryTool


def build_agent() -> LLMAgent:
    """Build full dependency graph with Naver adapter."""

    settings = get_settings()

    if not settings.naver_client_id or not settings.naver_client_secret:
        raise ValueError(
            "NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET이 필요합니다."
        )

    adapter = NaverMarineContentAdapter(
        client_id=settings.naver_client_id,
        client_secret=settings.naver_client_secret,
    )

    repository = MarineContentRepository()

    tool = MarineContentQueryTool(
        adapter=adapter,
        filtering_service=FilteringService(),
        normalization_service=NormalizationService(),
        repository=repository,
    )

    server = MCPServer(marine_query_tool=tool)

    client = MCPClient(
        server=server,
        tool_handler=ToolRequestHandler(),
        formatter=RequestFormatter(),
        session_manager=SessionManager(),
    )

    llm_provider = None
    if settings.llm_enabled and settings.llm_api_key:
        llm_provider = GeminiProvider(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )

    query_structurer = QueryStructurer(llm_provider=llm_provider)
    recommender = CandidateConstrainedRecommender(llm_provider=llm_provider)

    return LLMAgent(
        mcp_client=client,
        query_structurer=query_structurer,
        recommender=recommender,
    )