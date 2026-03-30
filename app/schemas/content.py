"""Schemas for marine content and candidate lists."""

from datetime import datetime

from pydantic import BaseModel, HttpUrl

from app.schemas.query import StructuredQuery


class MarineContentItem(BaseModel):
    """Internal normalized marine content item."""

    id: str
    service_name: str
    location: str
    activity: str
    price: int
    capacity: int
    available_start: datetime
    available_end: datetime
    transport_info: str | None = None
    source: str
    detail_url: HttpUrl | str
    thumbnail_url: HttpUrl | str | None = None
    description: str | None = None


class MCPSearchRequest(BaseModel):
    """Request body for candidate retrieval."""

    structured_query: StructuredQuery


class MCPSearchResponse(BaseModel):
    """Response body with candidate pool."""

    candidates: list[MarineContentItem]
    trace_id: str
