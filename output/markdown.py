"""Render a research run as a Markdown report."""
from pathlib import Path
from typing import List

from core import config
from core.logging import get_logger

log = get_logger("markdown")


def render(topic: str, results: List[dict]) -> str:
    """results: [{question, answer, score, verdict, reason, status, model_used, context}]."""
    lines = [f"# Research Report: {topic}", ""]
    passed = sum(1 for r in results if r["status"] == "done")
    lines.append(f"_Questions: {len(results)} | Passed: {passed} | Failed: {len(results) - passed}_")
    lines.append("")
    for i, r in enumerate(results, 1):
        badge = "PASS" if r["status"] == "done" else "FAILED"
        lines.append(f"## Q{i}. {r['question']}")
        lines.append(f"**Status:** {badge} | **Score:** {r['score']:.2f} | **Model:** {r['model_used']}")
        lines.append("")
        lines.append(r["answer"] or "_(no answer)_")
        lines.append("")
        if r.get("reason"):
            lines.append(f"> Reviewer: {r['reason']}")
            lines.append("")
    return "\n".join(lines)


def write(topic: str, results: List[dict], out_dir: Path = None, stem: str = "report") -> Path:
    out_dir = Path(out_dir or config.OUTPUTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stem}.md"
    path.write_text(render(topic, results), encoding="utf-8")
    log.info("Wrote Markdown report: %s", path)
    return path
