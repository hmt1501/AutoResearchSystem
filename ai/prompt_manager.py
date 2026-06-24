"""All prompt templates live here. Each builder returns (system, user) strings."""
from typing import List, Tuple


def question_generation(topic: str, n: int = 5) -> Tuple[str, str]:
    system = (
        "You are a research assistant. Given a topic, produce focused research "
        "questions that can be answered from a document collection. "
        'Respond ONLY with a JSON object of the form {"questions": ["...", "..."]}.'
    )
    user = f"Topic: {topic}\n\nGenerate {n} distinct research questions about this topic."
    return system, user


def query_rewrite(query: str) -> Tuple[str, str]:
    system = (
        "You rewrite a search query into alternative phrasings to improve retrieval. "
        'Respond ONLY with JSON of the form {"variants": ["...", "..."]} containing '
        "exactly 2 reworded variants (do not repeat the original)."
    )
    user = f"Original query: {query}"
    return system, user


def answer_generation(question: str, context: str) -> Tuple[str, str]:
    system = (
        "You answer questions using ONLY the provided context. "
        "If the context is insufficient, say so explicitly. Be accurate and concise, "
        "and do not invent facts that are not supported by the context."
    )
    user = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    return system, user


def review(question: str, answer: str, context: str) -> Tuple[str, str]:
    system = (
        "You are a strict reviewer. Judge whether the answer is correct, grounded in "
        "the context, and complete. Do NOT decide on retries. "
        'Respond ONLY with JSON: {"score": <float 0..1>, '
        '"verdict": "pass"|"fail", "reason": "<short explanation>"}.'
    )
    user = (
        f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer to review:\n{answer}\n\n"
        "Evaluate grounding, correctness and completeness."
    )
    return system, user


def chat(question: str, context: str, history_text: str = "") -> Tuple[str, str]:
    system = (
        "You are a helpful assistant answering questions about the user's documents. "
        "Use the provided context as your primary source. If the context does not "
        "cover the question, say so and answer from general knowledge only if clearly "
        "flagged as such. Be conversational and concise."
    )
    history_block = f"Conversation so far:\n{history_text}\n\n" if history_text else ""
    user = (
        f"{history_block}Context from documents:\n{context}\n\n"
        f"User question: {question}\n\nAnswer:"
    )
    return system, user


def auto_fix(question: str, answer: str, reason: str, context: str) -> Tuple[str, str]:
    system = (
        "You improve an existing answer based on reviewer feedback. "
        "Do NOT rewrite from scratch; keep what is correct and fix the issues raised. "
        "Use ONLY the provided context."
    )
    user = (
        f"Context:\n{context}\n\nQuestion: {question}\n\n"
        f"Current answer:\n{answer}\n\nReviewer feedback (what to fix):\n{reason}\n\n"
        "Provide the improved answer:"
    )
    return system, user
