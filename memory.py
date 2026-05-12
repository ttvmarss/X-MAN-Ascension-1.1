"""Long-term memory using SQLite with FTS5 full-text search."""
import sqlite3
import os
import time
from pathlib import Path
from typing import Optional


DB_PATH = Path(os.path.expanduser("~/Documents/JARVIS/memory.db"))


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            importance INTEGER DEFAULT 5,
            created_at REAL NOT NULL,
            accessed_at REAL NOT NULL,
            access_count INTEGER DEFAULT 0
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
        USING fts5(content, content=memories, content_rowid=id);

        CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
            INSERT INTO memories_fts(rowid, content) VALUES (new.id, new.content);
        END;
        CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, content)
            VALUES ('delete', old.id, old.content);
        END;
        CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, content)
            VALUES ('delete', old.id, old.content);
            INSERT INTO memories_fts(rowid, content) VALUES (new.id, new.content);
        END;

        CREATE TABLE IF NOT EXISTS session_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summary TEXT NOT NULL,
            created_at REAL NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def save_memory(content: str, category: str = "general", importance: int = 5):
    conn = _get_conn()
    now = time.time()
    conn.execute(
        "INSERT INTO memories (content, category, importance, created_at, accessed_at) VALUES (?,?,?,?,?)",
        (content, category, importance, now, now),
    )
    conn.commit()
    conn.close()


def search_memories(query: str, limit: int = 5) -> list[dict]:
    conn = _get_conn()
    now = time.time()
    rows = conn.execute(
        """SELECT m.id, m.content, m.category, m.importance, m.created_at
           FROM memories_fts f JOIN memories m ON f.rowid = m.id
           WHERE memories_fts MATCH ?
           ORDER BY rank
           LIMIT ?""",
        (query, limit),
    ).fetchall()
    ids = [r["id"] for r in rows]
    if ids:
        placeholders = ",".join("?" * len(ids))
        conn.execute(
            f"UPDATE memories SET accessed_at=?, access_count=access_count+1 WHERE id IN ({placeholders})",
            [now] + ids,
        )
        conn.commit()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_memories(limit: int = 10) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, content, category, importance, created_at FROM memories ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_session_summary(summary: str):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO session_summaries (summary, created_at) VALUES (?,?)",
        (summary, time.time()),
    )
    conn.commit()
    conn.close()


def get_recent_summaries(limit: int = 3) -> list[str]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT summary FROM session_summaries ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [r["summary"] for r in rows]


def format_memories_for_context(query: str) -> str:
    memories = search_memories(query, limit=5)
    if not memories:
        return ""
    lines = ["Relevant memories:"]
    for m in memories:
        lines.append(f"  - {m['content']}")
    return "\n".join(lines)


init_db()
