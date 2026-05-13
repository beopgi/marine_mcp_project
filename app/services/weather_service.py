"""Weather service for recommendation context."""

from app.adapters.kma_adapter import KMAAdapter
from app.schemas.location import LocationContext
from app.schemas.weather import WeatherContext, WeatherItem


class WeatherService:
    """Resolve KMA weather for a persisted location."""

    def __init__(self, adapter: KMAAdapter) -> None:
        self.adapter = adapter

    async def get_weather(self, location: LocationContext) -> WeatherContext | None:
        return await self.adapter.fetch_current_weather(location.latitude, location.longitude)

    def to_weather_items(self, weather: WeatherContext | None) -> list[WeatherItem]:
        if weather is None:
            return []
        time_label = weather.observed_at.strftime("%-I %p").lower() if weather.observed_at else None
        return [
            WeatherItem(
                time=time_label,
                temperature=round(weather.temperature) if weather.temperature is not None else None,
                sky=weather.sky,
                precipitation_type=weather.precipitation_type,
                wind_speed=weather.wind_speed,
            )
        ]
