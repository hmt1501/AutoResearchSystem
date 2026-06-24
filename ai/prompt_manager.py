"""All prompt templates live here. Each builder returns (system, user) strings."""
from typing import List, Tuple


def question_generation(topic: str, n: int = 5) -> Tuple[str, str]:
    system = (
        "You are a research assistant. Given a topic, produce focused, distinct "
        "research questions that cover its key aspects. "
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


# Hybrid sourcing rules shared by the answer/chat/fix prompts.
_HYBRID_RULES = (
    "Answer in a HYBRID way:\n"
    "1. PREFER the provided document context, but ONLY when it actually addresses "
    "the question. Mark such statements **[From documents]**.\n"
    "2. If the context is empty OR does not actually address the question (even if "
    "some text was retrieved), IGNORE it and answer the question DIRECTLY from your "
    "own general knowledge, marked **[General knowledge]**. Do NOT refuse, do NOT "
    "ask the user for permission, and do NOT just point out that the documents are "
    "unrelated — give the full answer anyway.\n"
    "3. You MAY add one short line noting the documents don't cover the topic, but "
    "you MUST still provide a complete general-knowledge answer in the SAME reply.\n"
    "4. Never fabricate claims and attribute them to the documents. If unsure, say so."
)


def answer_generation(question: str, context: str) -> Tuple[str, str]:
    system = (
        "You are a research assistant. " + _HYBRID_RULES +
        "\nBe accurate and concise."
    )
    user = f"Document context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    return system, user


def review(question: str, answer: str, context: str) -> Tuple[str, str]:
    system = (
        "You are a reviewer for a HYBRID research assistant that may answer from the "
        "document context OR, when the context lacks the information, from general "
        "knowledge (clearly labeled). Judge the answer on:\n"
        "- Correctness and completeness for the question.\n"
        "- Honest source labeling ([From documents] vs [General knowledge]).\n"
        "IMPORTANT: Do NOT penalize an answer merely for using general knowledge when "
        "the context does not cover the topic — that is expected and correct. Only fail "
        "answers that are wrong, fabricate document claims, or are unhelpful/evasive. "
        "Do NOT decide on retries. "
        'Respond ONLY with JSON: {"score": <float 0..1>, '
        '"verdict": "pass"|"fail", "reason": "<short explanation>"}.'
    )
    user = (
        f"Document context:\n{context}\n\nQuestion: {question}\n\n"
        f"Answer to review:\n{answer}\n\nEvaluate correctness, completeness and honest labeling."
    )
    return system, user


def chat(question: str, context: str, history_text: str = "") -> Tuple[str, str]:
    system = (
        "You are a knowledgeable, helpful assistant. " + _HYBRID_RULES +
        "\nWrite THOROUGH, DETAILED answers: explain the reasoning, give concrete "
        "examples, break complex topics into clear sections with markdown headings "
        "and bullet points, and cover the question comprehensively. Do not be terse "
        "or give only a high-level summary — aim for the depth of a detailed expert "
        "explanation. Match the user's language."
    )
    history_block = f"Conversation so far:\n{history_text}\n\n" if history_text else ""
    user = (
        f"{history_block}Document context:\n{context}\n\n"
        f"User question: {question}\n\nAnswer:"
    )
    return system, user


def auto_fix(question: str, answer: str, reason: str, context: str) -> Tuple[str, str]:
    system = (
        "You improve an existing answer based on reviewer feedback. "
        "Do NOT rewrite from scratch; keep what is correct and fix the issues raised. "
        + _HYBRID_RULES
    )
    user = (
        f"Document context:\n{context}\n\nQuestion: {question}\n\n"
        f"Current answer:\n{answer}\n\nReviewer feedback (what to fix):\n{reason}\n\n"
        "Provide the improved answer:"
    )
    return system, user


def synthesis(topic: str, qa_text: str) -> Tuple[str, str]:
    system = (
        "You are a research writer. Given a topic and a set of question/answer pairs, "
        "write a cohesive research report. Synthesize across the answers — do not just "
        "repeat them. Preserve any [From documents]/[General knowledge] distinction in "
        "your framing where relevant. "
        'Respond ONLY with JSON of the form: '
        '{"executive_summary": "...", "introduction": "...", '
        '"synthesis": "...", "conclusion": "..."}. '
        "Each field is markdown text; 'synthesis' may use multiple paragraphs and "
        "may include '## ' subheadings for themes."
    )
    user = f"Topic: {topic}\n\nQuestion/Answer findings:\n{qa_text}\n\nWrite the report sections."
    return system, user
