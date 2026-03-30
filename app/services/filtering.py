"""Filtering service for explicit-constraint candidate filtering."""

from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery


class FilteringService:
    """Apply first-pass filtering by location/activity/budget/people/time."""

    def filter_candidates(
        self,
        items: list[MarineContentItem],
        query: StructuredQuery,
    ) -> list[MarineContentItem]:
        filtered = items

        if query.location:
            filtered = [i for i in filtered if i.location == query.location]

        if query.activity:
            filtered = [i for i in filtered if i.activity == query.activity]

        if query.price_min is not None:
            filtered = [i for i in filtered if i.price >= query.price_min]

        if query.price_max is not None:
            filtered = [i for i in filtered if i.price <= query.price_max]

        if query.people_count is not None:
            filtered = [i for i in filtered if i.capacity >= query.people_count]

        if query.time and query.time.start_datetime and query.time.end_datetime:
            start = query.time.start_datetime
            end = query.time.end_datetime
            filtered = [
                i for i in filtered if i.available_start <= end and i.available_end >= start
            ]

        return filtered
