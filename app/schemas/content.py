"""Schemas for marine content and candidate lists."""

from pydantic import BaseModel, HttpUrl

from app.schemas.query import StructuredQuery


class MarineContentItem(BaseModel):
    """Internal normalized marine content item."""

    id: str
    service_name: str
    location: str
    activity: str

    category: str | None = None
    telephone: str | None = None
    address: str | None = None
    road_address: str | None = None
    mapx: str | None = None
    mapy: str | None = None

    transport_info: str | None = None
    source: str

    source_url: HttpUrl | str | None = None
    map_search_url: HttpUrl | str | None = None

    description: str | None = None


class MCPSearchRequest(BaseModel):
    """Request body for candidate retrieval."""

    structured_query: StructuredQuery


class MCPSearchResponse(BaseModel):
    """Response body with candidate pool."""

    candidates: list[MarineContentItem]
    trace_id: str