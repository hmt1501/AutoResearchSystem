"""Retrieval with similarity filtering and dedup.

Single source of truth for the similarity rule: keep chunks where
similarity >= SIMILARITY_THRESHOLD (similarity = 1 - cosine_distance).

Phase A: single query. Multi-query (query_rewriter variants) is layered on in
Phase B via retrieve_multi().
"""
from typing import List, Optional

from core import config
from core.logging import get_logger
from rag.vector_db import VectorDB

log = get_logger("retriever")


def _filter_and_dedup(hits: List[dict], top_k: int) -> List[str]:
    seen = set()
    kept = []
    for h in sorted(hits, key=lambda x: x["similarity"], reverse=True):
        if h["similarity"] < config.SIMILARITY_THRESHOLD:
            continue
        text = h["text"]
        if text in seen:
            continue
        seen.add(text)
        kept.append(text)
        if len(kept) >= top_k:
            break
    return kept


def retrieve(query: str, db: Optional[VectorDB] = None, top_k: int = None) -> List[str]:
    db = db or VectorDB()
    top_k = top_k or config.RETRIEVER_TOP_K
    hits = db.query(query, top_k=top_k)
    kept = _filter_and_dedup(hits, top_k)
    log.info("Retrieve '%s' -> %d/%d chunks above threshold", query[:50], len(kept), len(hits))
    return kept


def retrieve_multi(queries: List[str], db: Optional[VectorDB] = None, top_k: int = None) -> List[str]:
    """Query with several phrasings, merge, filter and dedup (Phase B multi-query)."""
    db = db or VectorDB()
    top_k = top_k or config.RETRIEVER_TOP_K
    all_hits: List[dict] = []
    for q in queries:
        all_hits.extend(db.query(q, top_k=top_k))
    kept = _filter_and_dedup(all_hits, top_k)
    log.info("Multi-retrieve %d queries -> %d chunks", len(queries), len(kept))
    return kept
