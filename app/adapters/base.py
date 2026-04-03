"""Adapter interface for external marine content providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.mcp.formatter import MCPToolRequest


class MarineContentAPIAdapter(ABC):
    """Abstract interface for fetching raw marine content data.

    역할:
    - formatter가 생성한 MCPToolRequest를 받아
      실제 외부 API 호출을 수행한다.
    - 반환값은 normalization 이전의 raw dict 리스트이다.
    """

    @abstractmethod
    def fetch_contents(self, request: MCPToolRequest) -> list[dict[str, Any]]:
        """Fetch raw contents from an external provider using MCPToolRequest."""
        raise NotImplementedError