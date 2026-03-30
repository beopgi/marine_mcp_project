"""Adapter interface for external marine content providers."""

from abc import ABC, abstractmethod

from app.schemas.query import StructuredQuery


class MarineContentAPIAdapter(ABC):
    """Abstract interface for fetching raw marine content data."""

    @abstractmethod
    def fetch_contents(self, query: StructuredQuery) -> list[dict]:
        """Fetch raw contents matching query hints from external data source."""
        raise NotImplementedError
