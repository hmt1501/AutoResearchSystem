"""Central configuration. Loads .env and exposes all tunable constants and paths."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
OUTPUTS_DIR = DATA_DIR / "outputs"
DB_PATH = DATA_DIR / "research.sqlite3"

for _p in (DOCUMENTS_DIR, VECTOR_STORE_DIR, OUTPUTS_DIR):
    _p.mkdir(parents=True, exist_ok=True)

# --- API ---------------------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# --- Models ------------------------------------------------------------------
# Only two models. Primary for everything; fallback only on the final retry.
# NOTE: verified against OpenRouter's live /models list. The spec's slugs
# (anthropic/claude-3-5-haiku, google/gemini-flash-2.5) no longer exist;
# claude-3.5-haiku is also gone. Current cheap Haiku is claude-haiku-4.5.
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "anthropic/claude-haiku-4.5")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "google/gemini-2.5-flash")

# Every task uses primary; only the last retry switches to fallback.
TASK_MODEL_MAP = {
    "question_generator": "primary",
    "query_rewriter": "primary",
    "reviewer": "primary",
    "answer_generator": "primary",
    "auto_fix": "primary",       # retry 1-2: still primary
    "auto_fix_final": "fallback",  # retry 3 (last): switch to Gemini
}

# --- Behaviour tuning --------------------------------------------------------
CONFIDENCE_THRESHOLD = 0.7
MAX_RETRY = 3
CHUNK_SIZE = 500       # approximate words per chunk
CHUNK_OVERLAP = 50     # approximate words of overlap
RETRIEVER_TOP_K = 5
# Keep chunks where (1 - cosine_distance) >= this. The spec suggested 0.6, but
# all-MiniLM-L6-v2 rarely scores relevant passages above ~0.55, so 0.6 starves
# the context. 0.3 is a sane default for this model; tune via .env if needed.
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_COLLECTION = "research_docs"

HTTP_TIMEOUT = 120.0
