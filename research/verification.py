"""The ONLY place that reads retry_count and decides the next step.

Decision contract (per spec):
  - "pass"     : verdict score >= CONFIDENCE_THRESHOLD
  - "retry"    : fail and retry_count <  MAX_RETRY - 1   (use primary model)
  - "fallback" : fail and retry_count == MAX_RETRY - 1   (use Gemini fallback)
  - "failed"   : retry_count >= MAX_RETRY
"""
from typing import Dict

from core import config


def decide(retry_count: int, verdict: Dict) -> str:
    score = float(verdict.get("score", 0.0))
    is_pass = verdict.get("verdict") == "pass" and score >= config.CONFIDENCE_THRESHOLD

    if is_pass:
        return "pass"
    if retry_count >= config.MAX_RETRY:
        return "failed"
    if retry_count < config.MAX_RETRY - 1:
        return "retry"
    # retry_count == MAX_RETRY - 1
    return "fallback"
