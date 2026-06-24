"""Improve an existing answer based on the reviewer's reason.

Important: this improves the prior answer rather than regenerating from scratch.
use_fallback=True switches to Gemini for the final retry.
"""
from ai import prompt_manager
from ai.ai_client import get_client


def fix(question: str, answer: str, reason: str, context: str, use_fallback: bool = False) -> str:
    system, user = prompt_manager.auto_fix(question, answer, reason, context)
    return get_client().chat(user, use_fallback=use_fallback, system=system).strip()
