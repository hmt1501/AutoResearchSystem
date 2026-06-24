"""Render a research run as a Word (.docx) report via python-docx."""
from pathlib import Path
from typing import List

from core import config
from core.logging import get_logger

log = get_logger("word")


def write(topic: str, results: List[dict], out_dir: Path = None, stem: str = "report") -> Path:
    from docx import Document

    out_dir = Path(out_dir or config.OUTPUTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stem}.docx"

    doc = Document()
    doc.add_heading(f"Research Report: {topic}", level=0)
    passed = sum(1 for r in results if r["status"] == "done")
    doc.add_paragraph(
        f"Questions: {len(results)} | Passed: {passed} | Failed: {len(results) - passed}"
    )

    for i, r in enumerate(results, 1):
        doc.add_heading(f"Q{i}. {r['question']}", level=1)
        badge = "PASS" if r["status"] == "done" else "FAILED"
        meta = doc.add_paragraph()
        meta.add_run(f"Status: {badge} | Score: {r['score']:.2f} | Model: {r['model_used']}").italic = True
        doc.add_paragraph(r["answer"] or "(no answer)")
        if r.get("reason"):
            note = doc.add_paragraph()
            note.add_run(f"Reviewer: {r['reason']}").italic = True

    doc.save(str(path))
    log.info("Wrote Word report: %s", path)
    return path
