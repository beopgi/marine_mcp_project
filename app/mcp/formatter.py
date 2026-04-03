"""Request formatter for converting StructuredQuery into MCP tool requests.

역할:
- StructuredQuery -> 외부 API 요청용 파라미터 변환
- MCP Client가 그대로 전달할 수 있는 공통 요청 객체 생성
- provider별(Naver Local / Marine public APIs) 요청 분기

주의:
- 네이버 지역 검색 API는 장소/업체 중심 API이므로, location/activity를 query로 조합한다.
- 해양수산부/국립해양조사원 API는 activity에 따라 별도 요청을 생성한다.
- 공공데이터 API의 최종 파라미터 key 이름은 실제 활용신청 후 Swagger/상세 명세에 맞춰
  adapter 계층에서 마지막으로 확정하는 것을 권장한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from app.schemas.query import StructuredQuery


ProviderType = Literal[
    "naver_local",
    "naver_shopping",
    "mof_fishing_index",
    "mof_travel_index",
    "mof_beach_index",
]


@dataclass(slots=True)
class MCPToolRequest:
    """Common request object passed across MCP layers."""

    tool_name: str
    provider: ProviderType
    endpoint: str
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RequestFormatter:
    """Convert StructuredQuery into one or more MCPToolRequest objects."""

    NAVER_DEFAULT_DISPLAY = 10
    NAVER_DEFAULT_START = 1
    NAVER_DEFAULT_SORT = "random"

    def build_requests(self, query: StructuredQuery) -> List[MCPToolRequest]:
        """Build all external requests needed for the given structured query.

        현재 정책:
        1. 네이버 지역 검색 요청은 항상 생성
        2. activity가 해양 환경 정보와 관련 있으면 보조 환경 요청을 추가 생성
        """
        requests: List[MCPToolRequest] = []

        requests.append(self._build_naver_local_request(query))

        marine_request = self._build_marine_environment_request(query)
        if marine_request is not None:
            requests.append(marine_request)

        return requests

    def _build_naver_local_request(self, query: StructuredQuery) -> MCPToolRequest:
        """Build Naver Local Search API request."""
        search_query = self._build_naver_local_query(query)

        params: Dict[str, Any] = {
            "query": search_query,
            "display": self.NAVER_DEFAULT_DISPLAY,
            "start": self.NAVER_DEFAULT_START,
            "sort": self.NAVER_DEFAULT_SORT,
        }

        metadata: Dict[str, Any] = {
            "source": "naver_local",
            "raw_location": self._safe_str(query.location),
            "raw_activity": self._safe_str(query.activity),
            "time_range": self._serialize_time_range(query),
            "price_min": query.price_min,
            "price_max": query.price_max,
            "people_count": query.people_count,
            "duration": self._safe_str(query.duration),
            "transport": self._safe_str(query.transport),
            "purpose": self._safe_str(query.purpose),
            "preference": self._safe_str(query.preference),
            "avoid": self._safe_str(query.avoid),
        }

        return MCPToolRequest(
            tool_name="marine_content_search",
            provider="naver_local",
            endpoint="/v1/search/local.json",
            method="GET",
            params=params,
            metadata=metadata,
        )

    def _build_marine_environment_request(
        self, query: StructuredQuery
    ) -> Optional[MCPToolRequest]:
        """Build marine environment lookup request based on activity.

        activity별 정책:
        - 낚시: 바다낚시지수
        - 해수욕/수영: 해수욕지수
        - 요트/보트/투어/관광: 바다여행지수
        """
        activity = (self._safe_str(query.activity) or "").lower()
        location = self._safe_str(query.location)

        if not activity:
            return None

        if any(keyword in activity for keyword in ["낚시", "fishing"]):
            return MCPToolRequest(
                tool_name="marine_environment_lookup",
                provider="mof_fishing_index",
                endpoint="MOF_FISHING_INDEX_ENDPOINT",
                method="GET",
                params={
                    "point_name": location,
                    "base_date": self._format_date_for_public_api(query),
                    "page_no": 1,
                    "num_of_rows": 20,
                },
                metadata={
                    "source": "mof_fishing_index",
                    "activity": query.activity,
                    "location": location,
                },
            )

        if any(keyword in activity for keyword in ["해수욕", "수영", "swim", "beach"]):
            return MCPToolRequest(
                tool_name="marine_environment_lookup",
                provider="mof_beach_index",
                endpoint="MOF_BEACH_INDEX_ENDPOINT",
                method="GET",
                params={
                    "beach_name": location,
                    "base_date": self._format_date_for_public_api(query),
                    "page_no": 1,
                    "num_of_rows": 20,
                },
                metadata={
                    "source": "mof_beach_index",
                    "activity": query.activity,
                    "location": location,
                },
            )

        if any(
            keyword in activity
            for keyword in ["요트", "보트", "투어", "관광", "travel", "yacht", "boat"]
        ):
            return MCPToolRequest(
                tool_name="marine_environment_lookup",
                provider="mof_travel_index",
                endpoint="MOF_TRAVEL_INDEX_ENDPOINT",
                method="GET",
                params={
                    "spot_name": location,
                    "base_datetime": self._format_datetime_for_public_api(query),
                    "page_no": 1,
                    "num_of_rows": 20,
                },
                metadata={
                    "source": "mof_travel_index",
                    "activity": query.activity,
                    "location": location,
                },
            )

        return None

    def _build_naver_local_query(self, query: StructuredQuery) -> str:
        """Compose a Naver Local search query string.

        전략:
        - location + activity만 사용
        - 키워드 확장 금지
        - 사용자 입력 표현 최대한 보존
        """
        location = self._safe_str(query.location)
        activity = self._safe_str(query.activity)

        parts: List[str] = []

        if location:
            parts.append(location)

        if activity:
            parts.append(activity)

        if parts:
            return " ".join(parts)

        return "해양 액티비티"

    def _format_date_for_public_api(self, query: StructuredQuery) -> Optional[str]:
        """Format start datetime as YYYYMMDD for public APIs."""
        dt = self._get_start_datetime(query)
        if dt is None:
            return None
        return dt.strftime("%Y%m%d")

    def _format_datetime_for_public_api(self, query: StructuredQuery) -> Optional[str]:
        """Format start datetime as YYYYMMDDHHMM for public APIs."""
        dt = self._get_start_datetime(query)
        if dt is None:
            return None
        return dt.strftime("%Y%m%d%H%M")

    def _get_start_datetime(self, query: StructuredQuery) -> Optional[datetime]:
        if query.time is None:
            return None
        return query.time.start_datetime

    def _get_end_datetime(self, query: StructuredQuery) -> Optional[datetime]:
        if query.time is None:
            return None
        return query.time.end_datetime

    def _serialize_time_range(self, query: StructuredQuery) -> Dict[str, Optional[str]]:
        """Serialize time window for metadata/debugging."""
        start = self._get_start_datetime(query)
        end = self._get_end_datetime(query)

        return {
            "start_datetime": start.isoformat() if start else None,
            "end_datetime": end.isoformat() if end else None,
        }

    @staticmethod
    def _safe_str(value: Any) -> Optional[str]:
        """Convert value to trimmed string or None."""
        if value is None:
            return None
        text = str(value).strip()
        return text if text else None

    @staticmethod
    def _unique_preserve_order(values: List[str]) -> List[str]:
        """Remove duplicates while preserving order."""
        result: List[str] = []
        seen: set[str] = set()

        for value in values:
            normalized = value.strip()
            if not normalized:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)

        return result