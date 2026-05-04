"""Home recommendation service for Flutter tag-based entrypoint."""

from __future__ import annotations

import logging

from app.agents.llm_agent import LLMAgent
from app.repositories.user_preference_repo import UserPreferenceRepository
from app.schemas.query import StructuredQuery
from app.schemas.recommendation import HomeRecommendationResponse

logger = logging.getLogger(__name__)


class HomeRecommendationService:
    """Build and execute tag-based home recommendation flow."""

    def __init__(
        self,
        agent: LLMAgent,
        user_preference_repository: UserPreferenceRepository,
    ) -> None:
        self.agent = agent
        self.user_preference_repository = user_preference_repository

    def recommend_home(self, user_id: int, location: str) -> HomeRecommendationResponse:
        """Return Flutter-oriented home recommendation payload."""
        clean_location = location.strip() or '부산'

        try:
            tag_scores = self.user_preference_repository.get_user_tag_scores(user_id)
            top_tags = self._select_top_tags(tag_scores)
            query = self._build_structured_query(clean_location, top_tags)

            trace_id, candidates = self.agent.search_candidates(query)
            logger.info('home recommendation search complete trace_id=%s candidates=%d', trace_id, len(candidates))

            if not candidates:
                return self._fallback_response(clean_location)

            recommendation = self.agent.recommend(
                user_input=self._build_user_input(clean_location, top_tags),
                query=query,
                candidates=candidates,
            )

            selected = next((c for c in candidates if c.service_name == recommendation.title), candidates[0])
            link = selected.map_search_url or selected.source_url

            return HomeRecommendationResponse(
                title=recommendation.title,
                message=self._build_message(top_tags),
                link=link,
                image_url=None,
                matched_tags=top_tags,
            )
        except Exception:
            logger.exception('home recommendation failed for user_id=%s location=%s', user_id, clean_location)
            return self._fallback_response(clean_location)

    def _select_top_tags(self, tag_scores: dict[str, int], limit: int = 3) -> list[str]:
        filtered = [(tag, score) for tag, score in tag_scores.items() if score > 0]
        filtered.sort(key=lambda item: item[1], reverse=True)
        return [tag for tag, _ in filtered[:limit]]

    def _build_structured_query(self, location: str, top_tags: list[str]) -> StructuredQuery:
        activity = top_tags[0] if top_tags else '해양 액티비티'
        purpose = top_tags[1] if len(top_tags) > 1 else None
        preference = top_tags[2] if len(top_tags) > 2 else None

        return StructuredQuery(
            location=location,
            activity=activity,
            purpose=purpose,
            preference=preference,
        )

    def _build_user_input(self, location: str, top_tags: list[str]) -> str:
        if top_tags:
            return ' '.join([location, *top_tags])
        return f'{location} 해양 액티비티'

    def _build_message(self, top_tags: list[str]) -> str:
        if len(top_tags) >= 2:
            return f'{top_tags[0]}와 {top_tags[1]} 콘텐츠를 자주 확인한 사용자에게 적합한 추천입니다.'
        if top_tags:
            return f'{top_tags[0]} 선호를 반영한 위치 기반 추천입니다.'
        return '현재 맞춤형 후보를 불러오지 못해 위치 기반 기본 추천을 제공합니다.'

    def _fallback_response(self, location: str) -> HomeRecommendationResponse:
        return HomeRecommendationResponse(
            title=f'{location} 해양 액티비티 추천',
            message='현재 맞춤형 후보를 불러오지 못해 위치 기반 기본 추천을 제공합니다.',
            link=None,
            image_url=None,
            matched_tags=[],
        )
