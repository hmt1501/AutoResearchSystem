"""Convert the .docx report to .pdf.

Strategy (Windows-friendly, no GTK/Pango):
  1. docx2pdf (uses an installed Microsoft Word via COM).
  2. LibreOffice headless (`soffice --convert-to pdf`) if Word is absent.
If neither backend is available, log a warning and return None — the run still
succeeds with .md and .docx.
"""
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from core import config
from core.logging import get_logger

log = get_logger("pdf")


def _try_docx2pdf(docx_path: Path, pdf_path: Path) -> bool:
    try:
        from docx2pdf import convert
    except Exception as e:  # noqa: BLE001
        log.info("docx2pdf unavailable (%s)", e)
        return False
    try:
        convert(str(docx_path), str(pdf_path))
        return pdf_path.exists()
    except Exception as e:  # noqa: BLE001 - typically no Word installed
        log.info("docx2pdf conversion failed (%s)", e)
        return False


def _try_libreoffice(docx_path: Path, pdf_path: Path) -> bool:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return False
    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir",
             str(pdf_path.parent), str(docx_path)],
            check=True, capture_output=True, timeout=180,
        )
        produced = pdf_path.parent / (docx_path.stem + ".pdf")
        if produced.exists() and produced != pdf_path:
            produced.replace(pdf_path)
        return pdf_path.exists()
    except Exception as e:  # noqa: BLE001
        log.info("LibreOffice conversion failed (%s)", e)
        return False


def write(docx_path: Path, out_dir: Path = None, stem: str = "report") -> Optional[Path]:
    docx_path = Path(docx_path)
    out_dir = Path(out_dir or config.OUTPUTS_DIR)
    pdf_path = out_dir / f"{stem}.pdf"

    if _try_docx2pdf(docx_path, pdf_path):
        log.info("Wrote PDF via docx2pdf: %s", pdf_path)
        return pdf_path
    if _try_libreoffice(docx_path, pdf_path):
        log.info("Wrote PDF via LibreOffice: %s", pdf_path)
        return pdf_path

    log.warning(
        "No PDF backend available (need MS Word for docx2pdf or LibreOffice). "
        "Skipping PDF; .md and .docx were still produced."
    )
    return None
