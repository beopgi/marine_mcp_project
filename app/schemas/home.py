"""Schemas for Flutter home dashboard endpoint."""

from pydantic import BaseModel, Field, HttpUrl, model_validator

from app.schemas.location import PublicLocationContext
from app.schemas.weather import WeatherContext, WeatherItem


class HomeDashboardRequest(BaseModel):
    """Request for DB-backed location/weather/recommendation dashboard."""

    user_id: int | None = None
    clerk_id: str | None = None
    user_input: str = Field(
        default="오늘 근처에서 할만한 해양 액티비티 추천해줘",
        min_length=1,
    )
    activity: str | None = None
    preference: str | None = None

    @model_validator(mode="after")
    def require_user_identifier(self) -> "HomeDashboardRequest":
        if self.user_id is None and not self.clerk_id:
            raise ValueError("user_id 또는 clerk_id가 필요합니다.")
        return self


class HomeDashboardRecommendation(BaseModel):
    """Flutter-compatible recommendation card payload."""

    title: str
    link: HttpUrl | str | None = None
    message: str
    image_url: HttpUrl | str | None = None
    matched_tags: list[str] = Field(default_factory=list)


class HomeDashboardResponse(BaseModel):
    """Weather + recommendation response for Flutter home screen."""

    user_id: int | None = None
    clerk_id: str | None = None
    location: PublicLocationContext
    weather: WeatherContext | None = None
    weather_items: list[WeatherItem] = Field(default_factory=list)
    recommendation: HomeDashboardRecommendation
