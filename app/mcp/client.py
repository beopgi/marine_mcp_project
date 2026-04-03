"""MCP client layer that mediates between agent and MCP server."""

from __future__ import annotations

from typing import Iterable

from app.mcp.formatter import MCPToolRequest, RequestFormatter
from app.mcp.server import MCPServer
from app.mcp.session import SessionManager
from app.mcp.tool_handler import ToolRequestHandler
from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery


class MCPClient:
    """Client-side MCP orchestration with separated responsibilities.

    역할:
    - StructuredQuery를 받아 formatter를 통해 MCPToolRequest 목록 생성
    - 세션(trace_id) 생성 및 요청 metadata에 trace 정보 주입
    - MCP Server에 각 요청을 순차 전달
    - 반환된 후보군을 하나의 리스트로 합쳐 반환
    """

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

    def search_candidates(
        self,
        query: StructuredQuery,
    ) -> tuple[str, list[MarineContentItem]]:
        """Create session, build MCP requests, execute them, and return candidates.

        흐름:
        1. session 생성
        2. formatter로부터 MCPToolRequest 목록 생성
        3. 각 요청에 trace/session metadata 주입
        4. server.handle_request(...) 호출
        5. 결과 후보군 병합 및 중복 제거
        """
        session = self.session_manager.create_session()
        trace_id = session.trace_id

        requests = self.formatter.build_requests(query)
        prepared_requests = [
            self._attach_trace_metadata(req, trace_id) for req in requests
        ]

        collected_candidates: list[MarineContentItem] = []

        for request in prepared_requests:
            self._validate_tool_request(request)

            result = self.server.handle_request(request)

            if not result:
                continue

            collected_candidates.extend(self._ensure_candidate_list(result))

        merged_candidates = self._deduplicate_candidates(collected_candidates)

        return trace_id, merged_candidates

    def _attach_trace_metadata(
        self,
        request: MCPToolRequest,
        trace_id: str,
    ) -> MCPToolRequest:
        """Attach trace/session metadata to outgoing MCP request."""
        request.metadata["trace_id"] = trace_id
        request.metadata["session_id"] = trace_id
        return request

    def _validate_tool_request(self, request: MCPToolRequest) -> None:
        """Validate request against tool handler before sending to server.

        주의:
        기존 구조를 살리기 위해 ToolRequestHandler를 완전히 제거하지 않고
        '선택'이 아니라 '검증' 역할로 둔다.
        """
        if hasattr(self.tool_handler, "validate_tool_name"):
            self.tool_handler.validate_tool_name(request.tool_name)
            return

        if hasattr(self.tool_handler, "is_supported_tool"):
            if not self.tool_handler.is_supported_tool(request.tool_name):
                raise ValueError(f"Unsupported tool: {request.tool_name}")
            return

        # fallback:
        # tool_handler가 아직 구버전(select_tool만 존재)이라면 별도 검증 없이 통과
        return

    def _ensure_candidate_list(
        self,
        result: object,
    ) -> list[MarineContentItem]:
        """Normalize server result into a list of MarineContentItem.

        server.handle_request(...)가
        - list[MarineContentItem]
        - tuple[str, list[MarineContentItem]]
        둘 중 어떤 형태를 반환하더라도 최대한 흡수하도록 처리한다.
        """
        if isinstance(result, list):
            return result

        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], list):
            return result[1]

        raise TypeError(
            "MCPServer.handle_request() must return list[MarineContentItem] "
            "or tuple[..., list[MarineContentItem]]"
        )

    def _deduplicate_candidates(
        self,
        candidates: Iterable[MarineContentItem],
    ) -> list[MarineContentItem]:
        """Deduplicate candidates while preserving order.

        가능한 경우 다음 우선순위로 dedup key를 사용:
        1. id
        2. product_id
        3. detail_url
        4. title + source 조합
        """
        deduped: list[MarineContentItem] = []
        seen_keys: set[str] = set()

        for item in candidates:
            dedup_key = self._build_candidate_key(item)
            if dedup_key in seen_keys:
                continue

            seen_keys.add(dedup_key)
            deduped.append(item)

        return deduped

    def _build_candidate_key(self, item: MarineContentItem) -> str:
        """Build a stable deduplication key from candidate item."""
        for attr_name in ("id", "product_id", "detail_url", "url", "link"):
            if hasattr(item, attr_name):
                value = getattr(item, attr_name)
                if value:
                    return f"{attr_name}:{value}"

        title = getattr(item, "title", None) or getattr(item, "service_name", None) or "unknown"
        source = getattr(item, "source", None) or "unknown"
        return f"title_source:{title}:{source}"