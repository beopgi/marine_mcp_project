"""DB location + KMA weather + existing recommendation pipeline for Flutter home."""

from __future__ import annotations

import logging

from app.agents.llm_agent import LLMAgent
from app.repositories.user_location_repo import LocationNotFoundError
from app.repositories.user_preference_repo import UserPreferenceRepository
from app.schemas.home import HomeDashboardRecommendation, HomeDashboardRequest, HomeDashboardResponse
from app.schemas.location import PublicLocationContext
from app.schemas.query import StructuredQuery
from app.services.location_context_service import LocationContextService
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class HomeDashboardService:
    """Compose the Flutter home dashboard response without replacing recommendation logic."""

    def __init__(
        self,
        agent: LLMAgent,
        location_context_service: LocationContextService,
        weather_service: WeatherService,
        user_preference_repository: UserPreferenceRepository,
    ) -> None:
        self.agent = agent
        self.location_context_service = location_context_service
        self.weather_service = weather_service
        self.user_preference_repository = user_preference_repository

    async def build_dashboard(self, request: HomeDashboardRequest) -> HomeDashboardResponse:
        """Resolve DB location, optional weather, and run existing candidate-constrained recommender."""
        location = await self.location_context_service.get_latest_location(
            user_id=request.user_id,
            clerk_id=request.clerk_id,
        )

        weather = await self.weather_service.get_weather(location)
        weather_items = self.weather_service.to_weather_items(weather)
        matched_tags = self._load_top_tags(request.user_id)
        query = self._build_structured_query(request, location, matched_tags)

        trace_id, candidates = self.agent.search_candidates(query)
        logger.info(
            "home dashboard candidate search complete trace_id=%s candidates=%d",
            trace_id,
            len(candidates),
        )

        if candidates:
            result = self.agent.recommend(
                user_input=request.user_input,
                query=query,
                candidates=candidates,
                weather_context=weather,
            )
            selected = next((candidate for candidate in candidates if candidate.service_name == result.title), None)
            recommendation = HomeDashboardRecommendation(
                title=result.title,
                link=(selected.map_search_url or selected.source_url) if selected else result.link,
                message=result.message,
                image_url=None,
                matched_tags=matched_tags,
            )
        else:
            recommendation = HomeDashboardRecommendation(
                title="추천 결과 없음",
                link=None,
                message="현재 위치와 조건에 맞는 해양 액티비티 후보를 찾지 못했습니다.",
                image_url=None,
                matched_tags=matched_tags,
            )

        return HomeDashboardResponse(
            user_id=location.user_id or request.user_id,
            clerk_id=location.clerk_id or request.clerk_id,
            location=PublicLocationContext(
                latitude=location.latitude,
                longitude=location.longitude,
                region=location.region,
                address=location.address,
                recorded_at=location.recorded_at,
            ),
            weather=weather,
            weather_items=weather_items,
            recommendation=recommendation,
        )

    def _build_structured_query(
        self,
        request: HomeDashboardRequest,
        location,
        matched_tags: list[str],
    ) -> StructuredQuery:
        region = self._location_text(location.region, location.address)
        activity = request.activity or (matched_tags[0] if matched_tags else "해양 액티비티")
        preference = request.preference or (matched_tags[1] if len(matched_tags) > 1 else None)
        purpose = matched_tags[2] if len(matched_tags) > 2 else None
        return StructuredQuery(
            location=region,
            activity=activity,
            preference=preference,
            purpose=purpose,
        )

    def _location_text(self, region: str | None, address: str | None) -> str:
        if region and region.strip():
            return region.strip()
        if address and address.strip():
            return address.strip().split()[0]
        return "부산"

    def _load_top_tags(self, user_id: int | None, limit: int = 3) -> list[str]:
        if user_id is None:
            return []
        tag_scores = self.user_preference_repository.get_user_tag_scores(user_id)
        filtered = [(tag, score) for tag, score in tag_scores.items() if score > 0]
        filtered.sort(key=lambda item: item[1], reverse=True)
        return [tag for tag, _ in filtered[:limit]]


__all__ = ["HomeDashboardService", "LocationNotFoundError"]
