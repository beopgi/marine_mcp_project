"""In-memory repository storing latest candidate pool per trace id."""

from collections import defaultdict

from app.schemas.content import MarineContentItem


class MarineContentRepository:
    """Simple repository abstraction (swap with SQLite later if needed)."""

    def __init__(self) -> None:
        self._storage: dict[str, list[MarineContentItem]] = defaultdict(list)

    def save_candidates(self, trace_id: str, items: list[MarineContentItem]) -> None:
        """Persist candidate pool for a trace/session."""

        self._storage[trace_id] = items

    def get_candidates(self, trace_id: str) -> list[MarineContentItem]:
        """Retrieve candidate pool by trace id."""

        return self._storage.get(trace_id, [])
