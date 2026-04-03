"""Filtering service for explicit-constraint candidate filtering."""

from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery


class FilteringService:
    """Apply minimal filtering for candidate retrieval."""

    EXCLUDE_KEYWORDS = [
        "채비",
        "미끼",
        "장갑",
        "토시",
        "통발",
        "바늘",
        "루어",
        "웜",
        "낚시용품",
        "세트",
        "소품",
        "도구",
        "부품",
        "키트",
    ]

    def filter_candidates(
        self,
        items: list[MarineContentItem],
        query: StructuredQuery,
    ) -> list[MarineContentItem]:

        filtered = items

        filtered = [
            i for i in filtered
            if not any(
                keyword in (i.service_name or "")
                for keyword in self.EXCLUDE_KEYWORDS
            )
        ]

        if query.location:
            filtered = [
                i for i in filtered
                if i.location and query.location in i.location
            ]

        if query.activity:
            filtered = [
                i for i in filtered
                if i.activity and query.activity in i.activity
            ]

        return filtered