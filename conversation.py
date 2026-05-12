"""Conversation state management with three-tier memory."""
import time
from typing import Optional
import memory as mem_store


MAX_BUFFER = 20       # messages before rolling summary kicks in
SUMMARY_KEEP = 10     # messages to keep after summarizing


class ConversationManager:
    def __init__(self, user_name: str = "sir"):
        self.user_name = user_name
        self.buffer: list[dict] = []
        self.rolling_summary: str = ""
        self.session_start = time.time()
        # Load recent past summaries for context
        past = mem_store.get_recent_summaries(limit=2)
        if past:
            self.rolling_summary = "From previous sessions: " + " | ".join(past)

    def add_user(self, text: str):
        self.buffer.append({"role": "user", "content": text})
        self._maybe_compress()

    def add_assistant(self, text: str):
        self.buffer.append({"role": "assistant", "content": text})

    def get_messages(self) -> list[dict]:
        return list(self.buffer)

    def get_system_prompt(self, extra_context: str = "") -> str:
        parts = [
            f"You are JARVIS — Just A Rather Very Intelligent System. "
            f"You are a witty, competent AI assistant running on Windows 10. "
            f"Address the user as '{self.user_name}'. "
            f"Be concise, dry, and British. Keep voice responses under 3 sentences unless asked for detail. "
            f"You have access to the user's calendar, email, notes, and can build software, browse the web, and manage tasks.",
        ]
        if self.rolling_summary:
            parts.append(self.rolling_summary)
        if extra_context:
            parts.append(extra_context)
        return "\n\n".join(parts)

    def _maybe_compress(self):
        if len(self.buffer) >= MAX_BUFFER:
            self._compress()

    def _compress(self):
        old = self.buffer[: MAX_BUFFER - SUMMARY_KEEP]
        self.buffer = self.buffer[MAX_BUFFER - SUMMARY_KEEP:]
        lines = [f"{m['role'].upper()}: {m['content']}" for m in old]
        summary = "Earlier in this session: " + " | ".join(lines[:8])
        if self.rolling_summary:
            self.rolling_summary = self.rolling_summary + " || " + summary
        else:
            self.rolling_summary = summary

    def end_session(self):
        if not self.buffer:
            return
        lines = [f"{m['role']}: {m['content']}" for m in self.buffer[-6:]]
        summary = f"Session {time.strftime('%Y-%m-%d')}: " + " | ".join(lines)
        mem_store.save_session_summary(summary)
