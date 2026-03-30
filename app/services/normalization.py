"""Normalization service for mapping raw adapter payloads into canonical schema."""

from app.schemas.content import MarineContentItem


class NormalizationService:
    """Convert heterogeneous adapter records to `MarineContentItem` schema."""

    def normalize_items(self, raw_items: list[dict]) -> list[MarineContentItem]:
        normalized: list[MarineContentItem] = []
        for raw in raw_items:
            normalized.append(MarineContentItem(**raw))
        return normalized
