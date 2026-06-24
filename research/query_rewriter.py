"""Rewrite a query into variants for multi-query retrieval (primary model)."""
import json
from typing import List

from ai import prompt_manager
from ai.ai_client import get_client
from core.logging import get_logger

log = get_logger("query_rewriter")


def rewrite(query: str) -> List[str]:
    """Return [original, variant1, variant2]. Falls back to [original] on error."""
    system, user = prompt_manager.query_rewrite(query)
    try:
        raw = get_client().chat(user, use_fallback=False, system=system, json_mode=True)
        data = json.loads(raw) if raw.strip().startswith("{") else _loose(raw)
        variants = [str(v).strip() for v in data.get("variants", []) if str(v).strip()]
    except Exception as e:  # noqa: BLE001 - retrieval still works with just the original
        log.warning("Query rewrite failed (%s); using original only.", e)
        variants = []
    return [query] + variants[:2]


def _loose(raw: str) -> dict:
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(raw[start:end + 1])
    return {}
