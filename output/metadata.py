"""Write a JSON sidecar with run metadata."""
import json
from pathlib import Path
from typing import List

from core import config
from core.logging import get_logger

log = get_logger("metadata")


def write(topic: str, task_id: str, results: List[dict], timestamp: str,
          out_dir: Path = None, stem: str = "report") -> Path:
    out_dir = Path(out_dir or config.OUTPUTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stem}.meta.json"

    passed = sum(1 for r in results if r["status"] == "done")
    meta = {
        "topic": topic,
        "task_id": task_id,
        "timestamp": timestamp,
        "primary_model": config.PRIMARY_MODEL,
        "fallback_model": config.FALLBACK_MODEL,
        "questions_total": len(results),
        "questions_passed": passed,
        "questions_failed": len(results) - passed,
        "results": [
            {
                "question": r["question"],
                "status": r["status"],
                "score": r["score"],
                "model_used": r["model_used"],
            }
            for r in results
        ],
    }
    path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Wrote metadata: %s", path)
    return path
