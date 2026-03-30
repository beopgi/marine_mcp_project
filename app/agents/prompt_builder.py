"""Prompt builder for controlled recommendation phase."""

from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery


class RecommendationPromptBuilder:
    """Split recommendation prompt into role/task/format sections."""

    ROLE_PROMPT = (
        '너는 해양 레저 추천 시스템의 추천 모듈이다. '
        '반드시 제공된 후보군 내에서만 선택해야 하며, 후보군 외 항목을 생성하면 안 된다.'
    )

    TASK_PROMPT = (
        '사용자 질의와 각 후보의 속성을 비교하여 가장 적합한 단일 항목을 선택하라. '
        '명시적 제약 조건을 우선 적용한 뒤 의미적 적합도를 비교하라.'
    )

    FORMAT_PROMPT = (
        'JSON 형식으로만 응답하라: '
        '{"selected_id": "...", "reason": "...", "matched_constraints": ["..."]}'
    )

    def build(self, query: StructuredQuery, candidates: list[MarineContentItem]) -> str:
        """Build full prompt text for external LLM provider (optional path)."""

        return (
            f'[Role]\n{self.ROLE_PROMPT}\n\n'
            f'[Task]\n{self.TASK_PROMPT}\n\n'
            f'[Format]\n{self.FORMAT_PROMPT}\n\n'
            f'[Structured Query]\n{query.model_dump_json(indent=2)}\n\n'
            f'[Candidates]\n{[c.model_dump(mode="json") for c in candidates]}'
        )
