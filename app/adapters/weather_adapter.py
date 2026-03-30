"""Optional weather adapter placeholder for future ranking enhancements."""


class WeatherAdapter:
    """Stub weather integration point."""

    def get_weather_context(self, location: str) -> dict:
        """Return weather context for a location (not yet integrated)."""

        return {'location': location, 'status': 'not_implemented'}
