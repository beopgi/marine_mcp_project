"""MCP server layer that manages concrete tools."""

from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery
from app.tools.marine_content_query_tool import MarineContentQueryTool


class MCPServer:
    """Server-side MCP endpoint abstraction for tool execution."""

    def __init__(self, marine_query_tool: MarineContentQueryTool) -> None:
        self.marine_query_tool = marine_query_tool

    def handle_request(self, payload: dict) -> list[MarineContentItem]:
        """Parse payload and dispatch to designated tool."""

        tool_name = payload['tool_name']
        trace_id = payload['trace_id']
        query = StructuredQuery.model_validate(payload['query'])

        if tool_name == 'marine_content_query_tool':
            return self.marine_query_tool.run(query=query, trace_id=trace_id)

        raise ValueError(f'Unsupported tool requested: {tool_name}')
