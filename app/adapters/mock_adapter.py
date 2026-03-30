"""Mock adapter loading marine contents from local JSON."""

import json
from pathlib import Path

from app.adapters.base import MarineContentAPIAdapter
from app.schemas.query import StructuredQuery


class MockMarineContentAdapter(MarineContentAPIAdapter):
    """Load mock marine leisure content for offline development/demo."""

    def __init__(self, data_path: str = 'app/data/mock_marine_contents.json') -> None:
        self.data_path = Path(data_path)

    def fetch_contents(self, query: StructuredQuery) -> list[dict]:
        _ = query
        with self.data_path.open('r', encoding='utf-8') as f:
            return json.load(f)
