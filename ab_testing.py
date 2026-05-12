"""A/B testing framework for response strategy experiments."""
import json
import os
import random
import time
from pathlib import Path


AB_PATH = Path(os.path.expanduser("~/Documents/JARVIS/ab_tests.json"))


def _load() -> dict:
    if not AB_PATH.exists():
        return {"experiments": {}, "results": {}}
    try:
        return json.loads(AB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"experiments": {}, "results": {}}


def _save(data: dict):
    AB_PATH.parent.mkdir(parents=True, exist_ok=True)
    AB_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_variant(experiment: str, variants: list[str]) -> str:
    """Get a consistent variant for an experiment (assigned randomly, then sticky)."""
    data = _load()
    exps = data.get("experiments", {})
    if experiment not in exps:
        variant = random.choice(variants)
        exps[experiment] = {"variant": variant, "assigned_at": time.time()}
        data["experiments"] = exps
        _save(data)
        return variant
    return exps[experiment]["variant"]


def record_outcome(experiment: str, outcome: str, value: float = 1.0):
    data = _load()
    results = data.get("results", {})
    if experiment not in results:
        results[experiment] = []
    results[experiment].append({"outcome": outcome, "value": value, "at": time.time()})
    data["results"] = results
    _save(data)


def get_tts_speed() -> str:
    return get_variant("tts_speed", ["normal", "slightly_faster"])


def get_response_length() -> str:
    return get_variant("response_length", ["brief", "standard"])
