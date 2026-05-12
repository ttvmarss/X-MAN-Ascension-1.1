"""System evolution: track capability improvements and usage stats."""
import json
import os
import time
from pathlib import Path


EVOLUTION_PATH = Path(os.path.expanduser("~/Documents/JARVIS/evolution.json"))


def _load() -> dict:
    if not EVOLUTION_PATH.exists():
        return {"interactions": 0, "capabilities_used": {}, "started_at": time.time()}
    try:
        return json.loads(EVOLUTION_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"interactions": 0, "capabilities_used": {}, "started_at": time.time()}


def _save(data: dict):
    EVOLUTION_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVOLUTION_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_interaction(capability: str = "conversation"):
    data = _load()
    data["interactions"] = data.get("interactions", 0) + 1
    caps = data.get("capabilities_used", {})
    caps[capability] = caps.get(capability, 0) + 1
    data["capabilities_used"] = caps
    _save(data)


def get_stats() -> dict:
    data = _load()
    uptime_days = (time.time() - data.get("started_at", time.time())) / 86400
    return {
        "interactions": data.get("interactions", 0),
        "uptime_days": round(uptime_days, 1),
        "top_capabilities": sorted(
            data.get("capabilities_used", {}).items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5],
    }


def format_stats_for_speech() -> str:
    stats = get_stats()
    top = stats["top_capabilities"]
    cap_str = ", ".join(f"{c[0]} ({c[1]}x)" for c in top[:3]) if top else "general conversation"
    return (
        f"We've had {stats['interactions']} interactions over {stats['uptime_days']} days. "
        f"Most used capabilities: {cap_str}."
    )
