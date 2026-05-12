"""Task and reminder tracking with SQLite."""
import sqlite3
import os
import time
from pathlib import Path
from typing import Optional


DB_PATH = Path(os.path.expanduser("~/Documents/JARVIS/tasks.db"))


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            priority INTEGER DEFAULT 3,
            status TEXT DEFAULT 'pending',
            due_at REAL,
            created_at REAL NOT NULL,
            completed_at REAL
        );

        CREATE TABLE IF NOT EXISTS build_tasks (
            id TEXT PRIMARY KEY,
            prompt TEXT NOT NULL,
            project_dir TEXT,
            status TEXT DEFAULT 'running',
            output TEXT DEFAULT '',
            created_at REAL NOT NULL,
            completed_at REAL
        );
    """)
    conn.commit()
    conn.close()


def add_task(title: str, description: str = "", priority: int = 3, due_at: Optional[float] = None) -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO tasks (title, description, priority, due_at, created_at) VALUES (?,?,?,?,?)",
        (title, description, priority, due_at, time.time()),
    )
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return task_id


def get_pending_tasks() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE status='pending' ORDER BY priority DESC, due_at ASC NULLS LAST"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_task(task_id: int):
    conn = _get_conn()
    conn.execute(
        "UPDATE tasks SET status='done', completed_at=? WHERE id=?",
        (time.time(), task_id),
    )
    conn.commit()
    conn.close()


def register_build(task_id: str, prompt: str, project_dir: str = ""):
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO build_tasks (id, prompt, project_dir, created_at) VALUES (?,?,?,?)",
        (task_id, prompt, project_dir, time.time()),
    )
    conn.commit()
    conn.close()


def update_build(task_id: str, status: str, output: str = ""):
    conn = _get_conn()
    completed_at = time.time() if status in ("done", "failed") else None
    conn.execute(
        "UPDATE build_tasks SET status=?, output=?, completed_at=? WHERE id=?",
        (status, output, completed_at, task_id),
    )
    conn.commit()
    conn.close()


def get_build(task_id: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM build_tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


init_db()
