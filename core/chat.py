"""RAG chat orchestrator: a single question -> retrieve -> answer (with history).

Unlike task_manager (which auto-generates many questions and writes a report),
this answers one user message at a time, grounded in the document store, and
keeps short conversation history. No review/auto-fix loop — it's interactive.
"""
from typing import List, Optional, Tuple

from ai import prompt_manager
from ai.ai_client import get_client
from core.logging import get_logger
from rag.retriever import retrieve
from rag.vector_db import VectorDB

log = get_logger("chat")

# History is a list of (user_message, assistant_message) pairs.
History = List[Tuple[str, str]]


def _format_history(history: Optional[History], max_turns: int = 5) -> str:
    if not history:
        return ""
    recent = history[-max_turns:]
    lines = []
    for user_msg, bot_msg in recent:
        lines.append(f"User: {user_msg}")
        lines.append(f"Assistant: {bot_msg}")
    return "\n".join(lines)


class RagChat:
    def __init__(self, vector_db: Optional[VectorDB] = None):
        self.vdb = vector_db or VectorDB()

    def ask(self, question: str, history: Optional[History] = None) -> dict:
        """Return {"answer": str, "sources": [chunk_text, ...]}."""
        question = (question or "").strip()
        if not question:
            return {"answer": "Please enter a question.", "sources": []}

        if self.vdb.count() == 0:
            return {
                "answer": "No documents have been ingested yet. Add documents first.",
                "sources": [],
            }

        # Augment the retrieval query with the previous user turn so vague
        # follow-ups ("what are its risks?") still retrieve the right chunks.
        retrieval_query = question
        if history:
            retrieval_query = f"{history[-1][0]} {question}"
        chunks = retrieve(retrieval_query, db=self.vdb)
        context = "\n\n---\n\n".join(chunks) if chunks else "(no relevant context found)"
        history_text = _format_history(history)

        system, user = prompt_manager.chat(question, context, history_text)
        answer = get_client().chat(user, use_fallback=False, system=system).strip()

        log.info("Chat answered (%d source chunks)", len(chunks))
        return {"answer": answer, "sources": chunks}
