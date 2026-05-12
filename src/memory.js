// SQLite-backed long-term memory with FTS5 full-text search.
import Database from 'better-sqlite3'
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'
import { homedir } from 'node:os'

const DATA_DIR = join(homedir(), 'Documents', 'JARVIS')
mkdirSync(DATA_DIR, { recursive: true })

const db = new Database(join(DATA_DIR, 'memory.db'))
db.pragma('journal_mode = WAL')

db.exec(`
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
    INSERT INTO memories_fts(memories_fts, rowid, content) VALUES('delete', old.id, old.content);
  END;
  CREATE TABLE IF NOT EXISTS session_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary TEXT NOT NULL,
    created_at REAL NOT NULL
  );
  CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    priority INTEGER DEFAULT 3,
    status TEXT DEFAULT 'pending',
    due_at REAL,
    created_at REAL NOT NULL,
    completed_at REAL
  );
`)

export function saveMemory(content, category = 'general', importance = 5) {
  const now = Date.now() / 1000
  db.prepare(
    'INSERT INTO memories (content, category, importance, created_at, accessed_at) VALUES (?, ?, ?, ?, ?)'
  ).run(content, category, importance, now, now)
}

export function searchMemories(query, limit = 5) {
  try {
    return db
      .prepare(
        `SELECT m.id, m.content, m.category, m.importance
         FROM memories_fts f JOIN memories m ON f.rowid = m.id
         WHERE memories_fts MATCH ?
         ORDER BY rank LIMIT ?`
      )
      .all(query, limit)
  } catch {
    return []
  }
}

export function saveSummary(summary) {
  db.prepare('INSERT INTO session_summaries (summary, created_at) VALUES (?, ?)').run(
    summary,
    Date.now() / 1000
  )
}

export function getRecentSummaries(limit = 2) {
  return db
    .prepare('SELECT summary FROM session_summaries ORDER BY created_at DESC LIMIT ?')
    .all(limit)
    .map((r) => r.summary)
}

export function addTask(title, priority = 3, dueInHours = null) {
  const now = Date.now() / 1000
  const dueAt = dueInHours ? now + dueInHours * 3600 : null
  const res = db
    .prepare('INSERT INTO tasks (title, priority, due_at, created_at) VALUES (?, ?, ?, ?)')
    .run(title, priority, dueAt, now)
  return res.lastInsertRowid
}

export function getPendingTasks() {
  return db
    .prepare(
      "SELECT * FROM tasks WHERE status = 'pending' ORDER BY priority DESC, due_at ASC"
    )
    .all()
}

export function completeTask(id) {
  db.prepare(
    "UPDATE tasks SET status = 'done', completed_at = ? WHERE id = ?"
  ).run(Date.now() / 1000, id)
}
