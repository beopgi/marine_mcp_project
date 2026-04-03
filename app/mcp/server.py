"""MCP server layer that manages concrete tools."""

from __future__ import annotations

from typing import Any, Optional

from app.mcp.formatter import MCPToolRequest
from app.schemas.content import MarineContentItem
from app.tools.marine_content_query_tool import MarineContentQueryTool


class MCPServer:
    """Server-side MCP endpoint abstraction for tool execution.

    역할:
    - MCPClient가 전달한 MCPToolRequest를 받아 적절한 tool에 위임
    - tool_name 기준으로 분기
    - tool 실행 결과(list[MarineContentItem])를 반환

    지원 tool_name:
    - marine_content_search
    - marine_environment_lookup (optional)
    """

    def __init__(
        self,
        marine_query_tool: MarineContentQueryTool,
        marine_environment_tool: Optional[Any] = None,
    ) -> None:
        self.marine_query_tool = marine_query_tool
        self.marine_environment_tool = marine_environment_tool

    def handle_request(self, request: MCPToolRequest) -> list[MarineContentItem]:
        """Dispatch MCPToolRequest to the designated tool."""

        if not isinstance(request, MCPToolRequest):
            raise TypeError("request must be an instance of MCPToolRequest")

        tool_name = request.tool_name
        trace_id = request.metadata.get("trace_id")

        if tool_name == "marine_content_search":
            return self._run_marine_content_search(request, trace_id)

        if tool_name == "marine_environment_lookup":
            return self._run_marine_environment_lookup(request, trace_id)

        raise ValueError(f"Unsupported tool requested: {tool_name}")

    def _run_marine_content_search(
        self,
        request: MCPToolRequest,
        trace_id: Optional[str],
    ) -> list[MarineContentItem]:
        """Execute marine content search tool."""

        if not hasattr(self.marine_query_tool, "run"):
            raise AttributeError("marine_query_tool must implement run(...)")

        return self.marine_query_tool.run(
            request=request,
            trace_id=trace_id,
        )

    def _run_marine_environment_lookup(
        self,
        request: MCPToolRequest,
        trace_id: Optional[str],
    ) -> list[MarineContentItem]:
        """Execute marine environment lookup tool.

        marine_environment_tool이 아직 구현되지 않았다면 빈 리스트를 반환한다.
        이렇게 해두면 후보군 생성 파이프라인을 먼저 연결하고,
        환경 정보 연동은 나중에 붙일 수 있다.
        """

        if self.marine_environment_tool is None:
            return []

        if not hasattr(self.marine_environment_tool, "run"):
            raise AttributeError("marine_environment_tool must implement run(...)")

        return self.marine_environment_tool.run(
            request=request,
            trace_id=trace_id,
        )