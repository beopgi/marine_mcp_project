"""Schemas for weather context used by recommendation."""

from datetime import datetime

from pydantic import BaseModel


class WeatherContext(BaseModel):
    """Normalized KMA weather values used as recommendation context."""

    temperature: float | None = None
    precipitation_type: str | None = None
    precipitation_amount: float | None = None
    humidity: int | None = None
    wind_speed: float | None = None
    wind_direction: str | None = None
    sky: str | None = None
    observed_at: datetime | None = None


class WeatherItem(BaseModel):
    """Compact weather card item for Flutter home UI."""

    time: str | None = None
    temperature: int | None = None
    sky: str | None = None
    precipitation_type: str | None = None
    wind_speed: float | None = None
