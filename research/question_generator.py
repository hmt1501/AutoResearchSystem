"""Generate research questions for a topic (primary model, JSON output)."""
import json
from typing import List

from ai import prompt_manager
from ai.ai_client import get_client
from core.logging import get_logger

log = get_logger("question_generator")


def generate(topic: str, n: int = 5) -> List[str]:
    system, user = prompt_manager.question_generation(topic, n)
    raw = get_client().chat(user, use_fallback=False, system=system, json_mode=True)
    questions = _parse(raw)
    log.info("Generated %d question(s) for topic '%s'", len(questions), topic)
    return questions


def _parse(raw: str) -> List[str]:
    raw = raw.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[start:end + 1]) if start != -1 and end != -1 else {}
    questions = data.get("questions", []) if isinstance(data, dict) else []
    return [str(q).strip() for q in questions if str(q).strip()]
