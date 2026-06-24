"""Local CPU embeddings via sentence-transformers (no API, no tokens spent)."""
from typing import List

from core import config
from core.logging import get_logger

log = get_logger("embedding")

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        log.info("Loading embedding model %s (CPU)...", config.EMBEDDING_MODEL)
        _model = SentenceTransformer(config.EMBEDDING_MODEL, device="cpu")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]
