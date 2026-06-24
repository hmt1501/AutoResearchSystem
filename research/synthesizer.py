"""Synthesize a cohesive research report (summary/intro/synthesis/conclusion)
from the per-question Q&A results. Runs once after the question loop.
"""
import json
from typing import Dict, List

from ai import prompt_manager
from ai.ai_client import get_client
from core.logging import get_logger

log = get_logger("synthesizer")

_EMPTY = {"executive_summary": "", "introduction": "", "synthesis": "", "conclusion": ""}


def _build_qa_text(results: List[dict], max_chars: int = 8000) -> str:
    parts = []
    for i, r in enumerate(results, 1):
        parts.append(f"Q{i}: {r['question']}\nA{i}: {r['answer']}")
    text = "\n\n".join(parts)
    return text[:max_chars]


def synthesize(topic: str, results: List[dict]) -> Dict[str, str]:
    """Return {executive_summary, introduction, synthesis, conclusion}."""
    if not results:
        return dict(_EMPTY)

    qa_text = _build_qa_text(results)
    system, user = prompt_manager.synthesis(topic, qa_text)
    try:
        raw = get_client().chat(user, use_fallback=False, system=system, json_mode=True)
        data = json.loads(raw) if raw.strip().startswith("{") else _loose(raw)
        out = {k: str(data.get(k, "")).strip() for k in _EMPTY}
        log.info("Synthesis generated (%d chars total)", sum(len(v) for v in out.values()))
        return out
    except Exception as e:  # noqa: BLE001 - report still works without synthesis
        log.warning("Synthesis failed (%s); report will contain Q&A only.", e)
        return dict(_EMPTY)


def _loose(raw: str) -> dict:
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(raw[start:end + 1])
    return {}
