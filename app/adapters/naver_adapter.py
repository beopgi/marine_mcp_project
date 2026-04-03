"""Adapter for Naver Search API integration."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.adapters.base import MarineContentAPIAdapter
from app.mcp.formatter import MCPToolRequest

logger = logging.getLogger(__name__)


class NaverMarineContentAdapter(MarineContentAPIAdapter):
    """Adapter implementation for Naver Search API."""

    BASE_URL = "https://openapi.naver.com"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        timeout: float = 10.0,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout

    def fetch_contents(self, request: MCPToolRequest) -> list[dict[str, Any]]:
        """Call Naver Search API using MCPToolRequest."""

        if request.provider not in {"naver_local", "naver_shopping"}:
            return []

        url = f"{self.BASE_URL}{request.endpoint}"
        params = request.params or {}

        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

        logger.info(
            "[NaverAdapter] request | provider=%s | url=%s | params=%s | trace_id=%s",
            request.provider,
            url,
            params,
            request.metadata.get("trace_id"),
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params, headers=headers)
                response.raise_for_status()

                data = response.json()
                items = data.get("items", [])

                if not isinstance(items, list):
                    logger.warning("[NaverAdapter] unexpected response format")
                    return []

                logger.info(
                    "[NaverAdapter] response | provider=%s | item_count=%s",
                    request.provider,
                    len(items),
                )
                return items

        except httpx.HTTPError as e:
            logger.error("[NaverAdapter] HTTP error: %s", str(e))
            return []

        except Exception as e:
            logger.exception("[NaverAdapter] unexpected error: %s", str(e))
            return []