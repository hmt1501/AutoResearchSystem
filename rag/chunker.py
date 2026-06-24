"""Split text into overlapping chunks.

Chunk size is measured in words (an approximation of tokens) — good enough for
MVP retrieval. Swap to a real tokenizer (tiktoken) later if needed.
"""
from typing import List

from core import config


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap if overlap is not None else config.CHUNK_OVERLAP

    words = text.split()
    if not words:
        return []
    if chunk_size <= 0:
        return [" ".join(words)]

    step = max(1, chunk_size - overlap)
    chunks = []
    for start in range(0, len(words), step):
        chunk = words[start:start + chunk_size]
        if chunk:
            chunks.append(" ".join(chunk))
        if start + chunk_size >= len(words):
            break
    return chunks


def chunk_documents(documents: List[dict]) -> List[dict]:
    """documents: [{"source", "text"}] -> [{"id", "source", "text"}] of chunks."""
    out = []
    for doc in documents:
        for i, chunk in enumerate(chunk_text(doc["text"])):
            out.append({
                "id": f"{doc['source']}::chunk{i}",
                "source": doc["source"],
                "text": chunk,
            })
    return out
