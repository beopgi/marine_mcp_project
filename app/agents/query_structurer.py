# app/agents/query_structurer.py

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.query import StructuredQuery

settings = get_settings()

class QueryStructurer:
    """
    자연어 입력을 LLM을 통해 StructuredQuery로 변환한다.
    rule-based fallback은 사용하지 않는다.
    실패 시 예외를 발생시켜 상위 계층에서 처리하게 한다.
    """

    def __init__(self, llm_provider: Optional[Any] = None):
        self.llm_provider = llm_provider

    def structure(self, user_query: str) -> StructuredQuery:
        if not user_query or not user_query.strip():
            raise ValueError("user_query is empty")

        if not self._can_use_llm():
            raise RuntimeError("LLM is not available")

        result = self._try_llm_structuring(user_query)
        if result is None:
            raise RuntimeError("LLM structuring failed")

        return result

    def _can_use_llm(self) -> bool:
        return bool(
            settings.llm_enabled
            and settings.llm_api_key
            and self.llm_provider is not None
        )

    def _try_llm_structuring(self, user_query: str) -> Optional[StructuredQuery]:
        prompt = self._build_prompt(user_query)

        raw_response = self.llm_provider.generate(prompt)
        print("[QueryStructurer] raw_response:", raw_response)

        parsed = self._extract_json(raw_response)
        if parsed is None:
            raise ValueError("Failed to parse JSON from LLM response")

        return self._to_structured_query(parsed)

    def _build_prompt(self, user_query: str) -> str:
        now = datetime.now().astimezone().isoformat()

        return f"""
너는 해양 레저 추천 시스템의 질의 구조화 모듈이다.

역할:
- 사용자의 자연어 요청을 구조화된 JSON으로 변환한다.
- 자유로운 설명문을 출력하지 않는다.
- 반드시 JSON만 출력한다.

중요 규칙:
1. 출력은 반드시 JSON 객체 하나만 반환한다.
2. 사용자의 시간 표현이 상대적 표현인 경우(예: 오늘, 내일, 이번 주말, 다음 주),
   반드시 아래 기준 시각을 바탕으로 실제 절대 시간 범위로 변환한다.
3. "이번 주말"처럼 한글 표현을 그대로 넣지 말고,
   start_datetime / end_datetime에 실제 ISO 8601 datetime 문자열로 넣는다.
4. 명시되지 않은 필드는 null로 둔다.
5. location, activity 등은 사용자의 의도를 반영해 구조화한다.
6. 이 작업은 챗봇 응답이 아니라 질의 구조화 작업이다.

기준 시각:
{now}

출력 스키마:
{{
  "location": null,
  "activity": null,
  "time": {{
    "start_datetime": null,
    "end_datetime": null
  }},
  "price_min": null,
  "price_max": null,
  "people_count": null,
  "duration": null,
  "transport": null,
  "purpose": null,
  "preference": null,
  "avoid": null
}}

예시:
사용자 입력:
이번 주말에 부산에서 2명이서 10만원 이하로 낚시하고 싶어

출력 예시:
{{
  "location": "부산",
  "activity": "낚시",
  "time": {{
    "start_datetime": "2026-04-04T00:00:00+09:00",
    "end_datetime": "2026-04-05T23:59:59+09:00"
  }},
  "price_min": null,
  "price_max": 100000,
  "people_count": 2,
  "duration": null,
  "transport": null,
  "purpose": null,
  "preference": null,
  "avoid": null
}}

사용자 입력:
{user_query}
""".strip()

    def _extract_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
        text = raw_text.strip()

        code_block_match = re.search(r"```(?:json)?\s*(\{{.*?\}})\s*```", text, re.DOTALL)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1))
            except json.JSONDecodeError:
                pass

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and start < end:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                return None

        return None

    def _to_structured_query(self, data: Dict[str, Any]) -> StructuredQuery:
        try:
            return StructuredQuery.model_validate(data)
        except AttributeError:
            return StructuredQuery.parse_obj(data)
        except ValidationError as e:
            raise ValueError(f"StructuredQuery validation failed: {e}") from e