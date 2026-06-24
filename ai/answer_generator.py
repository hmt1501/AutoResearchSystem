"""Generate an answer to a question from retrieved context (primary model)."""
from ai import prompt_manager
from ai.ai_client import get_client
from core import config


def generate(question: str, context: str) -> str:
    system, user = prompt_manager.answer_generation(question, context)
    # answer_generator uses primary per TASK_MODEL_MAP.
    return get_client().chat(user, use_fallback=False, system=system).strip()
