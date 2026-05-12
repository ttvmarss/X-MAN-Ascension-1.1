"""Persistent Claude Code session management for ongoing projects."""
import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Optional


CLAUDE_CODE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")
PROJECTS_DIR = Path(os.getenv("PROJECTS_DIR", "") or os.path.expanduser("~/Documents/JARVIS Projects"))

_active_sessions: dict[str, dict] = {}


def list_sessions() -> list[dict]:
    return list(_active_sessions.values())


def start_session(project_path: str, initial_prompt: str = "") -> str:
    """Start a persistent Claude Code session for a project."""
    session_id = str(uuid.uuid4())[:8]
    path = Path(project_path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)

    cmd = [CLAUDE_CODE_PATH]
    if initial_prompt:
        cmd += ["--print", initial_prompt]

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
        _active_sessions[session_id] = {
            "id": session_id,
            "path": str(path),
            "proc": proc,
            "output": [],
            "started_at": time.time(),
            "status": "running",
        }
        threading.Thread(target=_read_output, args=(session_id, proc), daemon=True).start()
    except Exception as e:
        return f"Failed to start session: {e}"

    return session_id


def send_to_session(session_id: str, message: str) -> bool:
    session = _active_sessions.get(session_id)
    if not session or session["status"] != "running":
        return False
    try:
        proc = session["proc"]
        proc.stdin.write(message + "\n")
        proc.stdin.flush()
        return True
    except Exception:
        return False


def get_session_output(session_id: str) -> str:
    session = _active_sessions.get(session_id)
    if not session:
        return ""
    return "\n".join(session["output"][-50:])


def stop_session(session_id: str):
    session = _active_sessions.pop(session_id, None)
    if session:
        try:
            session["proc"].terminate()
        except Exception:
            pass


def _read_output(session_id: str, proc: subprocess.Popen):
    for line in proc.stdout:
        if session_id in _active_sessions:
            _active_sessions[session_id]["output"].append(line.rstrip())
    if session_id in _active_sessions:
        _active_sessions[session_id]["status"] = "done"
