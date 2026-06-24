"""Render a research run as a Markdown report."""
from pathlib import Path
from typing import List

from core import config
from core.logging import get_logger

log = get_logger("markdown")


def render(topic: str, results: List[dict], overview: dict = None) -> str:
    """results: [{question, answer, score, ...}]; overview: synthesis sections (optional)."""
    overview = overview or {}
    lines = [f"# Research Report: {topic}", ""]

    # --- Synthesized research report ---
    has_overview = False
    if overview.get("executive_summary"):
        lines += ["## Executive Summary", "", overview["executive_summary"], ""]
        has_overview = True
    if overview.get("introduction"):
        lines += ["## Introduction", "", overview["introduction"], ""]
        has_overview = True
    if overview.get("synthesis"):
        lines += ["## Key Findings & Analysis", "", overview["synthesis"], ""]
        has_overview = True
    if overview.get("conclusion"):
        lines += ["## Conclusion", "", overview["conclusion"], ""]
        has_overview = True

    # Fallback: if synthesis could not be produced, render the gathered findings
    # as plain prose (still no Q&A framing) so the report is never empty.
    if not has_overview:
        lines += ["## Findings", ""]
        for r in results:
            if r.get("answer"):
                lines += [r["answer"], ""]

    return "\n".join(lines)


def write(topic: str, results: List[dict], out_dir: Path = None,
          stem: str = "report", overview: dict = None) -> Path:
    out_dir = Path(out_dir or config.OUTPUTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stem}.md"
    path.write_text(render(topic, results, overview), encoding="utf-8")
    log.info("Wrote Markdown report: %s", path)
    return path
