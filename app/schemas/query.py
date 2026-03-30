"""Schemas for user queries and structured query representations."""

from datetime import datetime

from pydantic import BaseModel, Field


class TimeWindow(BaseModel):
    """Normalized date-time range extracted from natural language."""

    start_datetime: datetime | None = None
    end_datetime: datetime | None = None


class StructuredQuery(BaseModel):
    """Canonical query format used across MCP layers."""

    location: str | None = None
    activity: str | None = None
    time: TimeWindow | None = None
    price_min: int | None = None
    price_max: int | None = None
    people_count: int | None = None
    duration: str | None = None
    transport: str | None = None
    purpose: str | None = None
    preference: str | None = None
    avoid: str | None = None


class UserQueryRequest(BaseModel):
    """Request schema containing natural language user input."""

    user_input: str = Field(..., min_length=1)


class QueryStructureResponse(BaseModel):
    """Response for /query/structure endpoint."""

    structured_query: StructuredQuery
