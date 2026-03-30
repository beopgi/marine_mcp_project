"""Natural language to structured query conversion module."""

import re
from datetime import UTC, datetime, time, timedelta

from app.schemas.query import StructuredQuery, TimeWindow


class QueryStructurer:
    """Rule-based query structuring with optional future LLM augmentation."""

    LOCATIONS = ['부산', '제주', '여수', '속초', '인천', '강릉', '포항']
    ACTIVITIES = ['낚시', '요트', '보트', '서핑', '카약', '스노클링']

    def structure(self, user_input: str, now: datetime | None = None) -> StructuredQuery:
        """Extract core constraints from Korean natural language input."""

        now = now or datetime.now(tz=UTC)

        location = self._extract_keyword(user_input, self.LOCATIONS)
        activity = self._extract_keyword(user_input, self.ACTIVITIES)
        price_max = self._extract_price_max(user_input)
        people_count = self._extract_people_count(user_input)
        time_window = self._extract_time_window(user_input, now)

        return StructuredQuery(
            location=location,
            activity=activity,
            time=time_window,
            price_max=price_max,
            people_count=people_count,
        )

    @staticmethod
    def _extract_keyword(text: str, keywords: list[str]) -> str | None:
        for keyword in keywords:
            if keyword in text:
                return keyword
        return None

    @staticmethod
    def _extract_price_max(text: str) -> int | None:
        # Matches: 10만원 이하, 8만 원 이하
        manwon_match = re.search(r'(\d+)\s*만\s*원?\s*이하', text)
        if manwon_match:
            return int(manwon_match.group(1)) * 10000

        numeric_match = re.search(r'(\d{4,})\s*원\s*이하', text)
        if numeric_match:
            return int(numeric_match.group(1))
        return None

    @staticmethod
    def _extract_people_count(text: str) -> int | None:
        match = re.search(r'(\d+)\s*명', text)
        if match:
            return int(match.group(1))
        return None

    def _extract_time_window(self, text: str, now: datetime) -> TimeWindow | None:
        if '이번 주말' in text:
            return self._this_weekend(now)
        if '내일' in text:
            tomorrow = (now + timedelta(days=1)).date()
            return TimeWindow(
                start_datetime=datetime.combine(tomorrow, time.min, tzinfo=UTC),
                end_datetime=datetime.combine(tomorrow, time.max, tzinfo=UTC),
            )
        return None

    @staticmethod
    def _this_weekend(now: datetime) -> TimeWindow:
        days_until_saturday = (5 - now.weekday()) % 7
        saturday = (now + timedelta(days=days_until_saturday)).date()
        sunday = saturday + timedelta(days=1)
        return TimeWindow(
            start_datetime=datetime.combine(saturday, time.min, tzinfo=UTC),
            end_datetime=datetime.combine(sunday, time.max, tzinfo=UTC),
        )
