"""Marine content query tool used by MCP server."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from app.adapters.base import MarineContentAPIAdapter
from app.mcp.formatter import MCPToolRequest
from app.repositories.marine_content_repo import MarineContentRepository
from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery, TimeWindow
from app.services.filtering import FilteringService
from app.services.normalization import NormalizationService


class MarineContentQueryTool:
    """Fetch, normalize, filter, and persist marine leisure candidates."""

    def __init__(
        self,
        adapter: MarineContentAPIAdapter,
        filtering_service: FilteringService,
        normalization_service: NormalizationService,
        repository: MarineContentRepository,
    ) -> None:
        self.adapter = adapter
        self.filtering_service = filtering_service
        self.normalization_service = normalization_service
        self.repository = repository

    def run(
        self,
        request: MCPToolRequest,
        trace_id: Optional[str],
    ) -> list[MarineContentItem]:
        """Execute tool pipeline and return filtered candidate pool.

        흐름:
        1. adapter를 통해 provider별 raw 데이터 조회
        2. normalization 수행
        3. filtering 수행
        4. repository에 trace_id 기준 저장
        """

        print("\n========== [MarineContentQueryTool.run START] ==========")

        if request.tool_name != "marine_content_search":
            raise ValueError(
                f"MarineContentQueryTool cannot handle tool_name={request.tool_name}"
            )

        # -----------------------
        # 1. query context 복원
        # -----------------------
        query_context = self._build_query_context_from_request(request)

        print("[DEBUG] query_context:")
        print("  location:", query_context.location)
        print("  activity:", query_context.activity)
        print("  price_min:", query_context.price_min)
        print("  price_max:", query_context.price_max)
        print("  people_count:", query_context.people_count)

        if query_context.time:
            print("  time_start:", query_context.time.start_datetime)
            print("  time_end:", query_context.time.end_datetime)
        else:
            print("  time: None")

        # -----------------------
        # 2. raw fetch
        # -----------------------
        raw_items = self._fetch_raw_items(request)
        print(f"[DEBUG] raw_items count: {len(raw_items)}")

        if raw_items:
            sample = raw_items[0]
            print("[DEBUG] raw sample keys:", list(sample.keys()))

        # -----------------------
        # 3. normalization
        # -----------------------
        normalized_items = self.normalization_service.normalize_items(
            raw_items,
            query_context,
        )
        print(f"[DEBUG] normalized_items count: {len(normalized_items)}")

        if normalized_items:
            sample = normalized_items[0]
            print("[DEBUG] normalized sample:")
            print("  id:", sample.id)
            print("  name:", sample.service_name)
            print("  location:", sample.location)
            print("  activity:", sample.activity)
            print("  category:", sample.category)
            print("  telephone:", sample.telephone)
            print("  road_address:", sample.road_address)
            print("  source_url:", sample.source_url)
            print("  map_search_url:", sample.map_search_url)

        # -----------------------
        # 4. filtering
        # -----------------------
        filtered_items = self.filtering_service.filter_candidates(
            normalized_items,
            query_context,
        )
        print(f"[DEBUG] filtered_items count: {len(filtered_items)}")

        if filtered_items:
            sample = filtered_items[0]
            print("[DEBUG] filtered sample:")
            print("  name:", sample.service_name)
            print("  location:", sample.location)
            print("  activity:", sample.activity)
            print("  category:", sample.category)
            print("  address:", sample.road_address or sample.address)
            print("  map_search_url:", sample.map_search_url)

        # -----------------------
        # 5. repository 저장
        # -----------------------
        if trace_id:
            self.repository.add_candidates(trace_id=trace_id, items=filtered_items)
            print(f"[DEBUG] saved to repository (trace_id={trace_id})")

        print("========== [MarineContentQueryTool.run END] ==========\n")

        return filtered_items

    def _fetch_raw_items(self, request: MCPToolRequest) -> list[dict[str, Any]]:
        """Delegate external fetch to adapter.

        adapter는 provider/endpoint/params 기반으로 실제 API 호출을 수행해야 한다.
        """
        if hasattr(self.adapter, "fetch_contents"):
            return self.adapter.fetch_contents(request)

        raise AttributeError(
            "MarineContentAPIAdapter must implement fetch_contents(request: MCPToolRequest)"
        )

    def _build_query_context_from_request(
        self,
        request: MCPToolRequest,
    ) -> StructuredQuery:
        """Rebuild a StructuredQuery-like context from request metadata.

        filtering service가 기존 StructuredQuery를 입력으로 받는 구조를 유지하기 위해
        metadata를 기반으로 최소한의 query context를 복원한다.
        """
        metadata = request.metadata or {}
        time_range = metadata.get("time_range") or {}

        return StructuredQuery(
            location=self._safe_str(
                metadata.get("raw_location") or metadata.get("location")
            ),
            activity=self._safe_str(
                metadata.get("raw_activity") or metadata.get("activity")
            ),
            time=TimeWindow(
                start_datetime=self._parse_datetime(time_range.get("start_datetime")),
                end_datetime=self._parse_datetime(time_range.get("end_datetime")),
            )
            if time_range
            else None,
            price_min=metadata.get("price_min"),
            price_max=metadata.get("price_max"),
            people_count=metadata.get("people_count"),
            duration=self._safe_str(metadata.get("duration")),
            transport=self._safe_str(metadata.get("transport")),
            purpose=self._safe_str(metadata.get("purpose")),
            preference=self._safe_str(metadata.get("preference")),
            avoid=self._safe_str(metadata.get("avoid")),
        )

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        """Parse ISO datetime string into datetime object."""
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        text = str(value).strip()
        if not text:
            return None

        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None

    @staticmethod
    def _safe_str(value: Any) -> Optional[str]:
        """Convert value to stripped string or None."""
        if value is None:
            return None

        text = str(value).strip()
        return text if text else None