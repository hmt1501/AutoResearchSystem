"""Main research loop: topic -> questions -> answer/review/auto-fix -> persist -> export.

Control flow per question:
    rewrite -> retrieve -> answer -> review -> verification.decide
        pass     : save & next
        retry    : auto_fix (primary), re-review
        fallback : auto_fix (Gemini), re-review
        failed   : mark failed & next
"""
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from ai import answer_generator, reviewer
from core import config
from core.database import Database
from core.logging import get_logger
from output import markdown, metadata, pdf, word
from rag.retriever import retrieve_multi
from rag.vector_db import VectorDB
from research import auto_fix, query_rewriter, synthesizer, verification

log = get_logger("task_manager")

# Progress callback signature: (question_index, total, question, status_str)
ProgressFn = Optional[Callable[[int, int, str, str], None]]


class TaskManager:
    def __init__(self, db: Optional[Database] = None, vector_db: Optional[VectorDB] = None):
        self.db = db or Database()
        self.vdb = vector_db or VectorDB()

    def run(self, topic: str, n_questions: int = 5, progress: ProgressFn = None) -> dict:
        from research.topic_manager import TopicManager

        task_id = self.db.create_task(topic)
        self.db.update_task_status(task_id, "running")
        log.info("=== Research run task=%s topic=%s ===", task_id, topic)

        tm = TopicManager(topic)
        questions = tm.build_questions(n_questions)
        results: List[dict] = []

        for idx, question in enumerate(questions, 1):
            if progress:
                progress(idx, len(questions), question, "running")
            result = self._answer_one(task_id, question)
            results.append(result)
            if progress:
                progress(idx, len(questions), question, result["status"])

        overall = "done" if all(r["status"] == "done" for r in results) else "failed"
        self.db.update_task_status(task_id, overall)

        # Synthesize a cohesive report (summary/intro/synthesis/conclusion) from the Q&A.
        if progress:
            progress(len(questions), len(questions), "Synthesizing report", "running")
        overview = synthesizer.synthesize(topic, results)

        exports = self._export(topic, task_id, results, overview)
        log.info("=== Run complete task=%s status=%s ===", task_id, overall)
        return {"task_id": task_id, "topic": topic, "status": overall,
                "results": results, "overview": overview, "exports": exports}

    def _answer_one(self, task_id: str, question: str) -> dict:
        # 1. Multi-query retrieval
        queries = query_rewriter.rewrite(question)
        chunks = retrieve_multi(queries, db=self.vdb)
        context = "\n\n---\n\n".join(chunks) if chunks else "(no relevant context found)"

        # 2. Initial answer (primary)
        answer = answer_generator.generate(question, context)
        model_used = config.PRIMARY_MODEL
        retry_count = 0

        # 3. Review + correction loop
        while True:
            verdict = reviewer.judge(question, answer, context)
            decision = verification.decide(retry_count, verdict)
            log.info("Q='%s' retry=%d decision=%s", question[:60], retry_count, decision)

            if decision == "pass":
                status = "done"
                break
            if decision == "failed":
                status = "failed"
                break

            use_fallback = decision == "fallback"
            if use_fallback:
                model_used = config.FALLBACK_MODEL
            answer = auto_fix.fix(question, answer, verdict["reason"], context,
                                  use_fallback=use_fallback)
            retry_count += 1

        # 4. Persist (answer + context for audit, then the final review)
        answer_id = self.db.save_answer(task_id, question, answer, context, model_used)
        self.db.save_review(answer_id, verdict["score"], verdict["verdict"], verdict["reason"])

        return {
            "question": question,
            "answer": answer,
            "context": context,
            "score": verdict["score"],
            "verdict": verdict["verdict"],
            "reason": verdict["reason"],
            "status": status,
            "model_used": model_used,
            "retry_count": retry_count,
        }

    def _export(self, topic: str, task_id: str, results: List[dict],
                overview: dict = None) -> dict:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = f"report_{ts}"
        out_dir = Path(config.OUTPUTS_DIR)

        md_path = markdown.write(topic, results, out_dir, stem, overview)
        docx_path = word.write(topic, results, out_dir, stem, overview)
        pdf_path = pdf.write(docx_path, out_dir, stem)
        meta_path = metadata.write(topic, task_id, results, ts, out_dir, stem)

        return {
            "markdown": str(md_path),
            "docx": str(docx_path),
            "pdf": str(pdf_path) if pdf_path else None,
            "metadata": str(meta_path),
        }

    def close(self) -> None:
        self.db.close()
