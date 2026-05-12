"""File-based notes stored in ~/Documents/JARVIS Notes/."""
import os
import time
from datetime import datetime
from pathlib import Path


NOTES_PATH = Path(
    os.getenv("NOTES_PATH", "") or os.path.expanduser("~/Documents/JARVIS Notes")
)


def _ensure_path():
    NOTES_PATH.mkdir(parents=True, exist_ok=True)


def save_note(content: str, title: str = "") -> str:
    _ensure_path()
    timestamp = datetime.now()
    if not title:
        first_line = content.split("\n")[0][:50].strip()
        title = first_line if first_line else timestamp.strftime("Note %Y-%m-%d %H-%M")
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
    filename = f"{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_{safe_title}.txt"
    note_path = NOTES_PATH / filename
    note_path.write_text(
        f"# {title}\nCreated: {timestamp.strftime('%Y-%m-%d %H:%M')}\n\n{content}\n",
        encoding="utf-8",
    )
    return str(note_path)


def get_notes(search: str = "", limit: int = 10) -> list[dict]:
    _ensure_path()
    notes = []
    files = sorted(NOTES_PATH.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
            if search and search.lower() not in text.lower():
                continue
            lines = text.splitlines()
            title = lines[0].lstrip("# ").strip() if lines else f.stem
            preview = " ".join(lines[3:6]) if len(lines) > 3 else ""
            notes.append({
                "title": title,
                "filename": f.name,
                "path": str(f),
                "preview": preview[:200],
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            })
            if len(notes) >= limit:
                break
        except Exception:
            continue
    return notes


def format_notes_for_speech(notes: list[dict]) -> str:
    if not notes:
        return "No notes found, sir."
    titles = [n["title"] for n in notes[:5]]
    return f"You have {len(notes)} notes. Most recent: {'; '.join(titles)}."


def get_note_content(filename: str) -> str:
    note_path = NOTES_PATH / filename
    if not note_path.exists():
        return ""
    return note_path.read_text(encoding="utf-8")
