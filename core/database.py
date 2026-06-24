"""SQLite persistence for tasks, answers and reviews."""
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from core import config
from core.logging import get_logger

log = get_logger("database")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          TEXT PRIMARY KEY,
    topic       TEXT NOT NULL,
    status      TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS answers (
    id          TEXT PRIMARY KEY,
    task_id     TEXT REFERENCES tasks(id),
    question    TEXT NOT NULL,
    answer      TEXT NOT NULL,
    context     TEXT,
    model_used  TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id          TEXT PRIMARY KEY,
    answer_id   TEXT REFERENCES answers(id),
    score       REAL,
    verdict     TEXT,
    reason      TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _new_id() -> str:
    return uuid.uuid4().hex


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or config.DB_PATH)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    # --- tasks ---------------------------------------------------------------
    def create_task(self, topic: str) -> str:
        task_id = _new_id()
        self.conn.execute(
            "INSERT INTO tasks (id, topic, status, updated_at) VALUES (?, ?, 'pending', ?)",
            (task_id, topic, datetime.utcnow().isoformat()),
        )
        self.conn.commit()
        return task_id

    def update_task_status(self, task_id: str, status: str, retry_count: Optional[int] = None) -> None:
        if retry_count is None:
            self.conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status, datetime.utcnow().isoformat(), task_id),
            )
        else:
            self.conn.execute(
                "UPDATE tasks SET status = ?, retry_count = ?, updated_at = ? WHERE id = ?",
                (status, retry_count, datetime.utcnow().isoformat(), task_id),
            )
        self.conn.commit()

    # --- answers -------------------------------------------------------------
    def save_answer(self, task_id: str, question: str, answer: str,
                    context: str, model_used: str) -> str:
        answer_id = _new_id()
        self.conn.execute(
            "INSERT INTO answers (id, task_id, question, answer, context, model_used) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (answer_id, task_id, question, answer, context, model_used),
        )
        self.conn.commit()
        return answer_id

    # --- reviews -------------------------------------------------------------
    def save_review(self, answer_id: str, score: float, verdict: str, reason: str) -> str:
        review_id = _new_id()
        self.conn.execute(
            "INSERT INTO reviews (id, answer_id, score, verdict, reason) VALUES (?, ?, ?, ?, ?)",
            (review_id, answer_id, score, verdict, reason),
        )
        self.conn.commit()
        return review_id

    def close(self) -> None:
        self.conn.close()
