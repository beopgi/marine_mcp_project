"""Placeholder adapter for future Naver or public-data integration."""

import logging

import httpx

from app.adapters.base import MarineContentAPIAdapter
from app.schemas.query import StructuredQuery

logger = logging.getLogger(__name__)


class NaverMarineContentAdapter(MarineContentAPIAdapter):
    """Stub implementation to show real API adapter extension point."""

    def fetch_contents(self, query: StructuredQuery) -> list[dict]:
        # Placeholder for future integration. Intentionally returns [] to keep pipeline deterministic.
        logger.info('Naver adapter called (stub). query=%s', query.model_dump())
        # Example skeleton for future API call:
        # with httpx.Client(timeout=10) as client:
        #     resp = client.get('https://openapi.naver.com/v1/...', params={...}, headers={...})
        #     resp.raise_for_status()
        #     return resp.json().get('items', [])
        _ = httpx
        return []
