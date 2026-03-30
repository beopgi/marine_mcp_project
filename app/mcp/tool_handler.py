"""Tool routing logic for MCP client."""

from app.schemas.query import StructuredQuery


class ToolRequestHandler:
    """Decide which MCP tool should be used for a given structured query."""

    def select_tool(self, query: StructuredQuery) -> str:
        """Return tool name. Extend with policy/intent routing later."""

        _ = query
        return 'marine_content_query_tool'
