"""Dependency wiring for MCP prototype pipeline."""

from app.adapters.mock_adapter import MockMarineContentAdapter
from app.adapters.naver_adapter import NaverMarineContentAdapter
from app.agents.llm_agent import LLMAgent
from app.core.config import get_settings
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
    """Build full dependency graph with mock/real adapter mode switch."""

    settings = get_settings()
    adapter = (
        MockMarineContentAdapter()
        if settings.adapter_mode == 'mock'
        else NaverMarineContentAdapter()
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
    return LLMAgent(mcp_client=client)
