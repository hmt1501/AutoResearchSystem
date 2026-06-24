"""Load raw text from .txt, .md, .pdf and .docx files."""
from pathlib import Path
from typing import List

from core.logging import get_logger

log = get_logger("document_loader")


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_pdf(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _load_docx(path: Path) -> str:
    from docx import Document
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


_LOADERS = {
    ".txt": _load_text,
    ".md": _load_text,
    ".pdf": _load_pdf,
    ".docx": _load_docx,
}


def load_document(path: Path) -> str:
    path = Path(path)
    loader = _LOADERS.get(path.suffix.lower())
    if loader is None:
        log.warning("Unsupported file type, skipping: %s", path)
        return ""
    try:
        text = loader(path)
        log.info("Loaded %s (%d chars)", path.name, len(text))
        return text
    except Exception as e:  # noqa: BLE001 - want robustness across many file types
        log.error("Failed to load %s: %s", path, e)
        return ""


def load_documents(paths: List[Path]) -> List[dict]:
    """Return [{"source": filename, "text": ...}] for non-empty documents."""
    out = []
    for p in paths:
        text = load_document(p)
        if text.strip():
            out.append({"source": Path(p).name, "text": text})
    return out
