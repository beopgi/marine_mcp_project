"""Candidate-constrained recommendation engine."""

from __future__ import annotations

from typing import Any

from app.agents.prompt_builder import RecommendationPromptBuilder
from app.llm.gemini_provider import GeminiProvider
from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery
from app.schemas.recommendation import RecommendationResult
from app.schemas.weather import WeatherContext


class CandidateConstrainedRecommender:
    """Gemini-based top-1 recommender constrained to candidate pool only."""

    def __init__(
        self,
        llm_provider: GeminiProvider | None = None,
    ) -> None:
        self.prompt_builder = RecommendationPromptBuilder()
        self.llm_provider = llm_provider

    def recommend(
        self,
        user_input: str,
        query: StructuredQuery,
        candidates: list[MarineContentItem],
        weather_context: WeatherContext | None = None,
    ) -> RecommendationResult:
        """Select exactly one item from the candidate pool using Gemini."""

        if not candidates:
            return RecommendationResult(
                title="추천 결과 없음",
                link=None,
                message="조건에 맞는 후보가 없어 추천할 항목이 없습니다.",
            )

        if not self.llm_provider or not self.llm_provider.is_available():
            return self._fallback_recommend(query=query, candidates=candidates, weather_context=weather_context)

        prompt = self.prompt_builder.build(
            user_input=user_input,
            query=query,
            candidates=candidates,
            weather_context=weather_context,
        )

        try:
            result = self.llm_provider.generate_json(
                prompt=prompt,
                temperature=0.1,
            )

            print("[Recommender] raw llm response:", result)

            selected_title = self._extract_selected_title(result)
            selected_item = self._find_candidate_by_title(selected_title, candidates)
            message = self._extract_message(result, selected_item)
            link = self._extract_link(result, selected_item)

            return RecommendationResult(
                title=selected_item.service_name,
                link=link,
                message=message,
            )

        except Exception as e:
            print("[Recommender] recommendation failed, fallback used:", str(e))
            return self._fallback_recommend(query=query, candidates=candidates, weather_context=weather_context)

    def _extract_selected_title(self, result: dict[str, Any]) -> str:
        """Extract selected candidate title from Gemini JSON response."""
        title = result.get("title")

        if not isinstance(title, str) or not title.strip():
            raise ValueError("LLM response missing valid title")

        return title.strip()

    def _extract_message(
        self,
        result: dict[str, Any],
        selected_item: MarineContentItem,
    ) -> str:
        """Extract recommendation message from Gemini JSON response."""
        message = result.get("message")

        if isinstance(message, str) and message.strip():
            return message.strip()

        return (
            f"'{selected_item.service_name}'이(가) 사용자 질의와 "
            f"후보군 조건에 가장 적합한 항목으로 선택되었습니다."
        )

    def _extract_link(
        self,
        result: dict[str, Any],
        selected_item: MarineContentItem,
    ) -> str | None:
        """Extract and validate link from Gemini JSON response."""
        link = result.get("link")

        if link is None:
            return selected_item.map_search_url

        if not isinstance(link, str) or not link.strip():
            return selected_item.map_search_url

        link = link.strip()

        # 현재 구조에서는 정확히 map_search_url과 일치해야 함
        if selected_item.map_search_url and link == selected_item.map_search_url:
            return link

        # 다르면 후보군의 정답 링크로 고정
        return selected_item.map_search_url

    def _find_candidate_by_title(
        self,
        selected_title: str,
        candidates: list[MarineContentItem],
    ) -> MarineContentItem:
        """Find selected candidate in current candidate pool by exact title match."""
        normalized_title = selected_title.strip()

        for candidate in candidates:
            if candidate.service_name and candidate.service_name.strip() == normalized_title:
                return candidate

        raise ValueError(
            f"title not found in candidate pool: {selected_title}"
        )

    def _fallback_recommend(
        self,
        query: StructuredQuery,
        candidates: list[MarineContentItem],
        weather_context: WeatherContext | None = None,
    ) -> RecommendationResult:
        """
        Fallback recommendation when Gemini is unavailable or invalid.
        """
        if not candidates:
            return RecommendationResult(
                title="추천 결과 없음",
                link=None,
                message="조건에 맞는 후보가 없어 추천할 항목이 없습니다.",
            )

        scored = sorted(
            candidates,
            key=lambda item: self._fallback_score(item, query, weather_context),
            reverse=True,
        )
        top = scored[0]

        return RecommendationResult(
            title=top.service_name,
            link=top.map_search_url,
            message=(
                f"LLM 추천 결과를 사용할 수 없어 후보군 내부 규칙 기반으로 "
                f"'{top.service_name}'을(를) 최상위 항목으로 선택했습니다."
            ),
        )

    def _fallback_score(
        self,
        item: MarineContentItem,
        query: StructuredQuery,
        weather_context: WeatherContext | None = None,
    ) -> float:
        """Simple fallback score using only current available fields."""
        score = 0

        if query.location and item.location == query.location:
            score += 100

        if query.activity and item.activity == query.activity:
            score += 90

        combined_text = " ".join(
            filter(
                None,
                [
                    item.service_name,
                    item.category,
                    item.description,
                    item.address,
                    item.road_address,
                    item.transport_info,
                ],
            )
        ).lower()

        if query.preference and query.preference.lower() in combined_text:
            score += 30

        if query.purpose and query.purpose.lower() in combined_text:
            score += 20

        if query.avoid and query.avoid.lower() in combined_text:
            score -= 50

        score += self._weather_score_adjustment(item, weather_context)

        return score

    def _weather_score_adjustment(
        self,
        item: MarineContentItem,
        weather_context: WeatherContext | None,
    ) -> float:
        """Adjust fallback ranking with weather without removing candidates."""
        if weather_context is None:
            return 0.0

        adjustment = 0.0
        precipitation_type = weather_context.precipitation_type
        precipitation_amount = weather_context.precipitation_amount or 0.0
        wind_speed = weather_context.wind_speed or 0.0
        sky = weather_context.sky

        combined_text = " ".join(
            filter(
                None,
                [
                    item.service_name,
                    item.category,
                    item.description,
                    item.activity,
                ],
            )
        ).lower()
        outdoor_keywords = ["요트", "보트", "낚시", "크루즈", "서핑", "체험", "투어"]
        is_outdoor_marine = any(keyword in combined_text for keyword in outdoor_keywords)

        if precipitation_type in {"rain", "snow", "rain_snow", "drizzle", "drizzle_snow", "snow_flurry"}:
            adjustment -= 12.0 if is_outdoor_marine else 5.0

        if precipitation_amount > 0:
            adjustment -= min(10.0, precipitation_amount * 2.0)

        if wind_speed >= 8.0 and any(keyword in combined_text for keyword in ["요트", "보트", "낚시", "크루즈"]):
            adjustment -= 15.0

        if precipitation_type in {None, "none"} and precipitation_amount == 0 and sky in {None, "clear", "sunny", "cloudy"}:
            adjustment += 5.0 if is_outdoor_marine else 2.0

        return adjustment