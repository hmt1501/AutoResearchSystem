"""Thin OpenRouter client. The single place that talks to the LLM API.

Model selection is intentionally simple: primary for everything, fallback only
when use_fallback=True (the final retry). No other module needs to know slugs.
"""
import json
from typing import Optional

import httpx

from core import config
from core.logging import get_logger

log = get_logger("ai_client")


class AIClientError(RuntimeError):
    pass


class AIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.OPENROUTER_API_KEY

    def chat(
        self,
        prompt: str,
        use_fallback: bool = False,
        system: Optional[str] = None,
        json_mode: bool = False,
    ) -> str:
        if not self.api_key:
            raise AIClientError(
                "OPENROUTER_API_KEY is not set. Copy .env.example to .env and add your key."
            )

        model = config.FALLBACK_MODEL if use_fallback else config.PRIMARY_MODEL

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": model, "messages": messages}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        log.info("LLM call model=%s json_mode=%s", model, json_mode)
        try:
            resp = httpx.post(
                config.OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=config.HTTP_TIMEOUT,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            body = e.response.text[:500]
            raise AIClientError(f"OpenRouter HTTP {e.response.status_code}: {body}") from e
        except httpx.HTTPError as e:
            raise AIClientError(f"OpenRouter request failed: {e}") from e

        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise AIClientError(f"Unexpected OpenRouter response: {json.dumps(data)[:500]}") from e


# Module-level singleton for convenience.
_client: Optional[AIClient] = None


def get_client() -> AIClient:
    global _client
    if _client is None:
        _client = AIClient()
    return _client
