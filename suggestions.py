"""Proactive suggestion engine."""
import time
from datetime import datetime


def get_time_based_suggestions() -> list[str]:
    hour = datetime.now().hour
    suggestions = []
    if 8 <= hour < 9:
        suggestions.append("Good morning. Shall I brief you on today's calendar and any overnight emails?")
    elif 12 <= hour < 13:
        suggestions.append("It's midday, sir. Would you like a status update on your tasks?")
    elif 17 <= hour < 18:
        suggestions.append("End of business approaching. Shall I summarize what was accomplished today?")
    elif 22 <= hour or hour < 6:
        suggestions.append("Working late, sir? I can prepare a brief for tomorrow if you'd like.")
    return suggestions


def get_pending_task_suggestions(tasks: list[dict]) -> list[str]:
    if not tasks:
        return []
    overdue = []
    now = time.time()
    for t in tasks:
        due = t.get("due_at")
        if due and due < now:
            overdue.append(t["title"])
    if overdue:
        return [f"You have {len(overdue)} overdue task(s): {', '.join(overdue[:3])}."]
    high_priority = [t for t in tasks if t.get("priority", 0) >= 4]
    if high_priority:
        return [f"High-priority item pending: {high_priority[0]['title']}."]
    return []
