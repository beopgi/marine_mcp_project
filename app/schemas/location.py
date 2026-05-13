"""Schemas for persisted user location context."""

from datetime import datetime

from pydantic import BaseModel, Field


class LocationContext(BaseModel):
    """Latest location stored by the Spring Boot user/location backend."""

    user_id: int | None = None
    clerk_id: str | None = None
    latitude: float
    longitude: float
    region: str | None = None
    address: str | None = None
    accuracy_m: float | None = None
    recorded_at: datetime | None = None


class PublicLocationContext(BaseModel):
    """Flutter-facing subset of the latest location context."""

    latitude: float
    longitude: float
    region: str | None = None
    address: str | None = None
    recorded_at: datetime | None = None
