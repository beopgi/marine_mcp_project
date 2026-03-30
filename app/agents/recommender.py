"""Candidate-constrained recommendation engine."""

from app.agents.prompt_builder import RecommendationPromptBuilder
from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery
from app.schemas.recommendation import RecommendationResult


class CandidateConstrainedRecommender:
    """Deterministic recommender with LLM-prompt extension point."""

    def __init__(self) -> None:
        self.prompt_builder = RecommendationPromptBuilder()

    def recommend(
        self,
        user_input: str,
        query: StructuredQuery,
        candidates: list[MarineContentItem],
    ) -> RecommendationResult:
        """Select top-1 from candidate pool only using explicit constraints + relevance scoring."""

        if not candidates:
            return RecommendationResult(
                selected_id=None,
                reason='조건에 맞는 후보가 없어 추천할 항목이 없습니다.',
                matched_constraints=[],
            )

        # Prompt is built for future external LLM usage. Current prototype uses deterministic ranking.
        _prompt = self.prompt_builder.build(query, candidates)
        _ = _prompt

        scored = sorted(candidates, key=lambda c: self._score_item(c, query, user_input), reverse=True)
        top = scored[0]

        matched_constraints = self._matched_constraints(top, query)
        reason = f"'{top.service_name}'가 위치/활동/예산/인원 조건 적합도가 가장 높습니다."

        return RecommendationResult(
            selected_id=top.id,
            reason=reason,
            matched_constraints=matched_constraints,
        )

    def _score_item(self, item: MarineContentItem, query: StructuredQuery, user_input: str) -> int:
        score = 0
        if query.location and item.location == query.location:
            score += 100
        if query.activity and item.activity == query.activity:
            score += 90
        if query.price_max is not None and item.price <= query.price_max:
            score += 70
        if query.people_count is not None and item.capacity >= query.people_count:
            score += 60

        # Lightweight semantic signal for MVP.
        if item.description and query.activity and query.activity in item.description:
            score += 20
        if item.description and any(token in item.description for token in user_input.split() if len(token) > 1):
            score += 10
        return score

    @staticmethod
    def _matched_constraints(item: MarineContentItem, query: StructuredQuery) -> list[str]:
        matched = []
        if query.location and item.location == query.location:
            matched.append('location')
        if query.activity and item.activity == query.activity:
            matched.append('activity')
        if query.price_max is not None and item.price <= query.price_max:
            matched.append('budget')
        if query.people_count is not None and item.capacity >= query.people_count:
            matched.append('people_count')
        return matched
