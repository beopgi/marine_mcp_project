"""Gemini LLM provider wrapper."""

from __future__ import annotations

import json
import logging
from typing import Any

import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiProvider:
    """Thin wrapper around Gemini API for structured JSON generation."""

    def __init__(
        self,
        api_key: str | None,
        model: str | None = None,
        model_name: str | None = None,
        enabled: bool = True,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name or model or "gemini-1.5-flash"
        self.enabled = enabled and bool(api_key)

        if self.enabled:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None

    def is_available(self) -> bool:
        """Return whether external LLM calls are currently available."""
        return self.enabled and self.model is not None

    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """
        Request JSON-only output from Gemini and parse it.

        Raises:
            RuntimeError: if provider is disabled or response parsing fails.
        """
        if not self.is_available():
            raise RuntimeError("Gemini provider is disabled or API key is missing.")

        logger.info("LLM call started. model=%s", self.model_name)

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "response_mime_type": "application/json",
                },
            )
        except Exception as e:
            logger.exception("Gemini API call failed.")
            raise RuntimeError(f"Gemini API call failed: {e}") from e

        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned empty response text.")

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            logger.exception("Failed to parse Gemini JSON response. raw=%s", text)
            raise RuntimeError(f"Failed to parse Gemini JSON response: {e}") from e

        logger.info("LLM call finished successfully.")
        return parsed

    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
    ) -> str:
        """
        Compatibility method for existing code paths that expect a string response.
        Returns JSON text as a string.
        """
        parsed = self.generate_json(prompt=prompt, temperature=temperature)
        return json.dumps(parsed, ensure_ascii=False)