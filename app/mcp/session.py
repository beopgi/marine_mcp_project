"""Session management for MCP client traces."""

import uuid
from dataclasses import dataclass


@dataclass
class MCPSession:
    """Represents one MCP interaction session."""

    trace_id: str


class SessionManager:
    """Creates and tracks MCP trace identifiers."""

    def create_session(self) -> MCPSession:
        """Generate a new session with unique trace ID."""

        return MCPSession(trace_id=f'trace_{uuid.uuid4().hex[:12]}')
