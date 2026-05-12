"""Learning system: track user preferences and interaction patterns."""
import json
import os
import time
from pathlib import Path


PREFS_PATH = Path(os.path.expanduser("~/Documents/JARVIS/preferences.json"))


def _load() -> dict:
    if not PREFS_PATH.exists():
        return {"preferences": {}, "patterns": {}}
    try:
        return json.loads(PREFS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"preferences": {}, "patterns": {}}


def _save(data: dict):
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def set_preference(key: str, value: str):
    data = _load()
    data["preferences"][key] = {"value": value, "set_at": time.time()}
    _save(data)


def get_preference(key: str) -> str | None:
    data = _load()
    entry = data["preferences"].get(key)
    return entry["value"] if entry else None


def record_pattern(action: str):
    data = _load()
    hour = time.strftime("%H")
    pattern_key = f"{action}_{hour}"
    data["patterns"][pattern_key] = data["patterns"].get(pattern_key, 0) + 1
    _save(data)


def get_all_preferences() -> dict:
    data = _load()
    return {k: v["value"] for k, v in data["preferences"].items()}


def format_preferences_for_context() -> str:
    prefs = get_all_preferences()
    if not prefs:
        return ""
    lines = [f"  - {k}: {v}" for k, v in list(prefs.items())[:10]]
    return "User preferences:\n" + "\n".join(lines)
