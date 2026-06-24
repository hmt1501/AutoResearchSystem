"""Offline tests — no OpenRouter API key required.

Covers chunking, embedding, vector store round-trip, retrieval similarity
filtering, and the verification decision logic.

Run:  python -m tests.test_offline
or:   pytest tests/test_offline.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import config
from rag import chunker
from research import verification


def test_chunker_overlap():
    text = " ".join(f"w{i}" for i in range(1200))
    chunks = chunker.chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) >= 2
    first = chunks[0].split()
    second = chunks[1].split()
    assert len(first) == 500
    # Overlap: last 50 words of chunk0 == first 50 words of chunk1
    assert first[-50:] == second[:50]
    print("PASS test_chunker_overlap")


def test_verification_logic():
    cfg_max = config.MAX_RETRY  # 3
    fail = {"score": 0.2, "verdict": "fail", "reason": "x"}
    ok = {"score": 0.9, "verdict": "pass", "reason": "good"}

    assert verification.decide(0, ok) == "pass"
    assert verification.decide(0, fail) == "retry"          # < MAX_RETRY-1
    assert verification.decide(cfg_max - 2, fail) == "retry"
    assert verification.decide(cfg_max - 1, fail) == "fallback"  # == MAX_RETRY-1
    assert verification.decide(cfg_max, fail) == "failed"
    # Pass verdict but score below threshold -> not a pass
    assert verification.decide(0, {"score": 0.5, "verdict": "pass"}) == "retry"
    print("PASS test_verification_logic")


def test_embedding_and_retrieval():
    """Heavier test: loads the embedding model and ChromaDB. Skips if libs missing."""
    try:
        from rag.vector_db import VectorDB
        from rag.retriever import retrieve
    except Exception as e:  # noqa: BLE001
        print(f"SKIP test_embedding_and_retrieval (import failed: {e})")
        return

    docs = [{
        "source": "t.md",
        "text": (
            "AI analyzes medical images like X-rays and MRIs to detect tumors. "
            "AlphaFold predicts protein folding for drug discovery. "
            "The capital of France is Paris and croissants are tasty."
        ),
    }]
    chunks = chunker.chunk_documents(docs)
    # Force tiny chunks so we get several distinct ones to retrieve over.
    chunks = []
    for i, sent in enumerate(docs[0]["text"].split(". ")):
        chunks.append({"id": f"t::c{i}", "source": "t.md", "text": sent})

    # Use a throwaway collection so the test never pollutes the real store.
    vdb = VectorDB(collection_name="test_offline_tmp")
    vdb.reset()
    vdb.add_chunks(chunks)
    results = retrieve("How does AI detect tumors in medical images?", db=vdb)
    assert results, "Expected at least one chunk above similarity threshold"
    joined = " ".join(results).lower()
    assert "tumor" in joined or "image" in joined
    print(f"PASS test_embedding_and_retrieval ({len(results)} chunks)")
    vdb.reset()  # clean up the temp collection


if __name__ == "__main__":
    test_chunker_overlap()
    test_verification_logic()
    test_embedding_and_retrieval()
    print("\nAll offline tests passed.")
