"""Repository for storing candidate pools by trace id."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from app.schemas.content import MarineContentItem


class MarineContentRepository:
    """In-memory repository for candidate pools.

    현재 역할:
    - trace_id 단위로 후보군 저장
    - 여러 MCP 요청 결과를 같은 trace_id 아래 누적 가능
    - 중복 제거된 후보군 조회 가능

    추후 SQLite/Redis 등으로 교체하기 쉽도록 인터페이스를 단순하게 유지한다.
    """

    def __init__(self) -> None:
        self._storage: dict[str, list[MarineContentItem]] = defaultdict(list)

    def save_candidates(self, trace_id: str, items: list[MarineContentItem]) -> None:
        """Replace candidate pool for a trace/session."""
        self._storage[trace_id] = self._deduplicate(items)

    def add_candidates(self, trace_id: str, items: list[MarineContentItem]) -> None:
        """Append candidates to an existing trace/session pool."""
        existing = self._storage.get(trace_id, [])
        merged = [*existing, *items]
        self._storage[trace_id] = self._deduplicate(merged)

    def get_candidates(self, trace_id: str) -> list[MarineContentItem]:
        """Retrieve candidate pool by trace id."""
        return self._storage.get(trace_id, [])

    def clear_candidates(self, trace_id: str) -> None:
        """Remove candidate pool for a trace/session."""
        if trace_id in self._storage:
            del self._storage[trace_id]

    def has_candidates(self, trace_id: str) -> bool:
        """Check whether the trace/session has any stored candidates."""
        return bool(self._storage.get(trace_id))

    def _deduplicate(
        self,
        items: Iterable[MarineContentItem],
    ) -> list[MarineContentItem]:
        """Deduplicate candidates while preserving order.

        우선순위:
        1. id
        2. product_id
        3. detail_url
        4. url
        5. link
        6. title + source 조합
        """
        result: list[MarineContentItem] = []
        seen_keys: set[str] = set()

        for item in items:
            key = self._build_candidate_key(item)
            if key in seen_keys:
                continue

            seen_keys.add(key)
            result.append(item)

        return result

    def _build_candidate_key(self, item: MarineContentItem) -> str:
        """Build a stable key for candidate identity."""
        for attr_name in ("id", "product_id", "detail_url", "url", "link"):
            if hasattr(item, attr_name):
                value = getattr(item, attr_name)
                if value:
                    return f"{attr_name}:{value}"

        title = getattr(item, "title", None) or getattr(item, "service_name", None) or "unknown"
        source = getattr(item, "source", None) or "unknown"
        return f"title_source:{title}:{source}"