"""Marine content query tool used by MCP server."""

from app.adapters.base import MarineContentAPIAdapter
from app.repositories.marine_content_repo import MarineContentRepository
from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery
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

    def run(self, query: StructuredQuery, trace_id: str) -> list[MarineContentItem]:
        """Execute tool pipeline and return filtered candidate pool."""

        raw_items = self.adapter.fetch_contents(query)
        normalized_items = self.normalization_service.normalize_items(raw_items)
        filtered_items = self.filtering_service.filter_candidates(normalized_items, query)
        self.repository.save_candidates(trace_id=trace_id, items=filtered_items)
        return filtered_items
