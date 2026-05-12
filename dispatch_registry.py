"""Registry to track dispatched Claude Code tasks and avoid re-dispatching."""
import json
import os
import time
from pathlib import Path


REGISTRY_PATH = Path(os.path.expanduser("~/Documents/JARVIS/dispatch_registry.json"))


def _load() -> dict:
    if not REGISTRY_PATH.exists():
        return {}
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def register(project_key: str, task_id: str, prompt: str):
    data = _load()
    data[project_key] = {
        "task_id": task_id,
        "prompt": prompt,
        "dispatched_at": time.time(),
    }
    _save(data)


def get_recent(project_key: str, max_age_seconds: int = 3600) -> dict | None:
    data = _load()
    entry = data.get(project_key)
    if not entry:
        return None
    age = time.time() - entry.get("dispatched_at", 0)
    if age > max_age_seconds:
        return None
    return entry


def clear(project_key: str):
    data = _load()
    data.pop(project_key, None)
    _save(data)
