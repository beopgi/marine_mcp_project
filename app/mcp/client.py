"""MCP client layer that mediates between agent and MCP server."""

from app.mcp.formatter import RequestFormatter
from app.mcp.server import MCPServer
from app.mcp.session import SessionManager
from app.mcp.tool_handler import ToolRequestHandler
from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery


class MCPClient:
    """Client-side MCP orchestration with separated responsibilities."""

    def __init__(
        self,
        server: MCPServer,
        tool_handler: ToolRequestHandler,
        formatter: RequestFormatter,
        session_manager: SessionManager,
    ) -> None:
        self.server = server
        self.tool_handler = tool_handler
        self.formatter = formatter
        self.session_manager = session_manager

    def search_candidates(self, query: StructuredQuery) -> tuple[str, list[MarineContentItem]]:
        """Create session, format request, execute on MCP server, return trace and candidates."""

        session = self.session_manager.create_session()
        tool_name = self.tool_handler.select_tool(query)
        payload = self.formatter.format_search_request(query, session.trace_id, tool_name)
        candidates = self.server.handle_request(payload)
        return session.trace_id, candidates
