"""Request formatting module for MCP server payloads."""

from app.schemas.query import StructuredQuery


class RequestFormatter:
    """Build wire-level MCP request payload from structured query."""

    def format_search_request(self, query: StructuredQuery, trace_id: str, tool_name: str) -> dict:
        """Format search payload consumed by MCP server."""

        return {
            'trace_id': trace_id,
            'tool_name': tool_name,
            'query': query.model_dump(mode='json'),
        }
