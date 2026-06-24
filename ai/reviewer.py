"""Reviewer: judges an answer and returns a JSON verdict ONLY.

This module never decides whether to retry — that is research/verification.py's
sole responsibility. Here we only produce {score, verdict, reason}.
"""
import json
from typing import Dict

from ai import prompt_manager
from ai.ai_client import get_client
from core import config
from core.logging import get_logger

log = get_logger("reviewer")


def _coerce(raw: str) -> Dict:
    """Parse the model's JSON; tolerate stray text around the object."""
    raw = raw.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            data = json.loads(raw[start:end + 1])
        else:
            raise
    score = float(data.get("score", 0.0))
    verdict = str(data.get("verdict", "fail")).lower()
    if verdict not in ("pass", "fail"):
        verdict = "pass" if score >= config.CONFIDENCE_THRESHOLD else "fail"
    return {"score": score, "verdict": verdict, "reason": str(data.get("reason", ""))}


def judge(question: str, answer: str, context: str) -> Dict:
    system, user = prompt_manager.review(question, answer, context)
    raw = get_client().chat(user, use_fallback=False, system=system, json_mode=True)
    try:
        verdict = _coerce(raw)
    except (json.JSONDecodeError, ValueError) as e:
        log.warning("Could not parse reviewer JSON (%s); defaulting to fail. Raw: %s", e, raw[:200])
        verdict = {"score": 0.0, "verdict": "fail", "reason": "Unparseable reviewer response."}
    log.info("Review verdict=%s score=%.2f", verdict["verdict"], verdict["score"])
    return verdict
