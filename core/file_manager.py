"""Input document discovery and output directory helpers."""
from pathlib import Path
from typing import List

from core import config
from core.logging import get_logger

log = get_logger("file_manager")

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def list_documents(docs_dir: Path) -> List[Path]:
    """Return all supported document files under docs_dir."""
    docs_dir = Path(docs_dir)
    if not docs_dir.exists():
        log.warning("Documents directory does not exist: %s", docs_dir)
        return []
    files = [
        p for p in sorted(docs_dir.rglob("*"))
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    log.info("Found %d document(s) in %s", len(files), docs_dir)
    return files


def ensure_output_dirs() -> None:
    for d in (config.DOCUMENTS_DIR, config.VECTOR_STORE_DIR, config.OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
