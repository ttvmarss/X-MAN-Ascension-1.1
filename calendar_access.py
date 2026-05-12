"""Windows Calendar integration via Outlook COM or JSON fallback."""
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


FALLBACK_PATH = Path(os.path.expanduser("~/Documents/JARVIS/calendar.json"))
BACKEND = os.getenv("CALENDAR_BACKEND", "auto")


def _try_outlook() -> bool:
    try:
        import win32com.client  # noqa: F401
        return True
    except ImportError:
        return False


def _get_outlook_events(days_ahead: int = 7) -> list[dict]:
    import win32com.client
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    calendar = ns.GetDefaultFolder(9)  # 9 = olFolderCalendar
    items = calendar.Items
    items.IncludeRecurrences = True
    items.Sort("[Start]")

    now = datetime.now()
    end = now + timedelta(days=days_ahead)

    restriction = (
        f"[Start] >= '{now.strftime('%m/%d/%Y')}' AND [Start] <= '{end.strftime('%m/%d/%Y')}'"
    )
    items = items.Restrict(restriction)

    events = []
    for item in items:
        try:
            events.append({
                "subject": item.Subject,
                "start": str(item.Start),
                "end": str(item.End),
                "location": item.Location or "",
                "body": item.Body[:200] if item.Body else "",
            })
        except Exception:
            continue
    return events


def _get_file_events(days_ahead: int = 7) -> list[dict]:
    if not FALLBACK_PATH.exists():
        return []
    try:
        data = json.loads(FALLBACK_PATH.read_text(encoding="utf-8"))
        now = time.time()
        cutoff = now + days_ahead * 86400
        events = []
        for e in data.get("events", []):
            event_time = e.get("timestamp", 0)
            if now <= event_time <= cutoff:
                events.append(e)
        return events
    except Exception:
        return []


def get_calendar_events(days_ahead: int = 7) -> list[dict]:
    if BACKEND == "outlook" or (BACKEND == "auto" and _try_outlook()):
        try:
            return _get_outlook_events(days_ahead)
        except Exception:
            pass
    return _get_file_events(days_ahead)


def format_events_for_speech(events: list[dict]) -> str:
    if not events:
        return "Your calendar is clear for the next week, sir."
    lines = []
    for e in events[:10]:
        subject = e.get("subject", e.get("title", "Unnamed event"))
        start = e.get("start", "")
        location = e.get("location", "")
        line = f"{subject}"
        if start:
            line += f" at {start}"
        if location:
            line += f" in {location}"
        lines.append(line)
    return "Here's what I have on your schedule: " + "; ".join(lines) + "."


def add_calendar_event_file(title: str, timestamp: float, location: str = "", notes: str = ""):
    FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {"events": []}
    if FALLBACK_PATH.exists():
        try:
            data = json.loads(FALLBACK_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    data["events"].append({
        "title": title,
        "timestamp": timestamp,
        "start": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M"),
        "location": location,
        "notes": notes,
    })
    FALLBACK_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
