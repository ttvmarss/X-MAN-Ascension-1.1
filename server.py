"""
JARVIS Server — Windows 10 Edition
FastAPI WebSocket backend: voice loop, intent dispatch, TTS, memory.
"""
import asyncio
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Optional

import anthropic
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
FISH_API_KEY = os.getenv("FISH_API_KEY", "")
FISH_VOICE_ID = os.getenv("FISH_VOICE_ID", "3b554ef0ee6748e7a1bba6e6f87e4aea")
USER_NAME = os.getenv("USER_NAME", "sir")
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", "8000"))

# ── Local modules ─────────────────────────────────────────────────────────────
import memory as mem_store
import tracking
import evolution
import learning
from conversation import ConversationManager
from calendar_access import get_calendar_events, format_events_for_speech
from mail_access import get_unread_emails, format_emails_for_speech
from notes_access import save_note, get_notes, format_notes_for_speech
from actions import (
    open_url, open_browser, open_app, open_windows_terminal,
    spawn_claude_code_build, do_research, connect_to_project,
)
from planner import generate_plan, format_plan_for_speech
from screen import get_screen_context
from suggestions import get_time_based_suggestions, get_pending_task_suggestions
from templates import INTENT_SYSTEM, JARVIS_SYSTEM_BASE, ACTION_TAG_INSTRUCTIONS
from qa import sanitize_for_tts, check_response_quality

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="JARVIS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

@app.get("/")
async def index():
    index_path = FRONTEND_DIST / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"status": "JARVIS online", "note": "Run 'npm run build' in frontend/ for the UI."}

@app.get("/health")
async def health():
    return {"status": "online", "user": USER_NAME}

# ── Anthropic client ──────────────────────────────────────────────────────────
_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def call_claude_haiku(messages: list[dict], system: str, max_tokens: int = 400) -> str:
    loop = asyncio.get_event_loop()
    def _sync():
        resp = _anthropic.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return resp.content[0].text
    return await loop.run_in_executor(None, _sync)


async def call_claude_opus(messages: list[dict], system: str, max_tokens: int = 2000) -> str:
    loop = asyncio.get_event_loop()
    def _sync():
        resp = _anthropic.messages.create(
            model="claude-opus-4-7",
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return resp.content[0].text
    return await loop.run_in_executor(None, _sync)


# ── Intent classification ─────────────────────────────────────────────────────
async def classify_intent(text: str) -> dict:
    try:
        result = await call_claude_haiku(
            [{"role": "user", "content": text}],
            INTENT_SYSTEM,
            max_tokens=200,
        )
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(result[start:end])
    except Exception:
        pass
    return {"intent": "conversation", "entities": {}, "confidence": 0.5}


# ── TTS via Fish Audio ────────────────────────────────────────────────────────
async def text_to_speech(text: str) -> bytes | None:
    if not FISH_API_KEY or not text.strip():
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.fish.audio/v1/tts",
                headers={
                    "Authorization": f"Bearer {FISH_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "reference_id": FISH_VOICE_ID,
                    "format": "mp3",
                    "mp3_bitrate": 128,
                    "latency": "normal",
                },
            )
            if resp.status_code == 200:
                return resp.content
    except Exception as e:
        print(f"[TTS] Error: {e}")
    return None


# ── Action tag parser ─────────────────────────────────────────────────────────
ACTION_RE = re.compile(r"\[ACTION:([A-Z_]+):?(.*?)\]", re.DOTALL)


async def dispatch_action(tag: str, value: str, ws: WebSocket) -> Optional[str]:
    """Execute an action tag and return an optional follow-up message."""
    value = value.strip()

    if tag == "BUILD":
        task_id = spawn_claude_code_build(value)
        await ws.send_json({"type": "action", "action": "build_started", "task_id": task_id})
        evolution.record_interaction("build")
        return f"Building project: {value[:60]}. I'll notify you when it's complete, {USER_NAME}."

    elif tag == "BROWSE":
        open_browser(value)
        evolution.record_interaction("browse")
        return None

    elif tag == "RESEARCH":
        task_id = do_research(value)
        await ws.send_json({"type": "action", "action": "research_started", "task_id": task_id})
        evolution.record_interaction("research")
        return f"Research underway on: {value[:60]}. I'll have a report ready shortly."

    elif tag == "PROMPT_PROJECT":
        task_id = connect_to_project(value)
        evolution.record_interaction("prompt_project")
        return f"Connected Claude Code to {value}."

    elif tag == "ADD_TASK":
        parts = value.split("|")
        title = parts[0].strip()
        priority = int(parts[1].strip()) if len(parts) > 1 else 3
        task_id = tracking.add_task(title, priority=priority)
        evolution.record_interaction("task")
        return None

    elif tag == "REMEMBER":
        mem_store.save_memory(value, category="preference", importance=7)
        learning.set_preference(value.split(":")[0].strip(), value)
        return None

    elif tag == "NOTE":
        path = save_note(value)
        evolution.record_interaction("notes")
        return None

    elif tag == "PLAN":
        plan = generate_plan(value)
        return format_plan_for_speech(plan)

    elif tag == "OPEN":
        if value.startswith("http"):
            open_url(value)
        else:
            open_app(value)
        evolution.record_interaction("open_app")
        return None

    return None


# ── Core response pipeline ────────────────────────────────────────────────────
async def build_context(intent: dict, entities: dict) -> str:
    """Gather relevant context data based on intent."""
    parts = []

    screen = get_screen_context()
    if screen:
        parts.append(screen)

    query = entities.get("query", "")
    if query:
        mem_context = mem_store.format_memories_for_context(query)
        if mem_context:
            parts.append(mem_context)

    pref_context = learning.format_preferences_for_context()
    if pref_context:
        parts.append(pref_context)

    intent_name = intent.get("intent", "conversation")

    if intent_name == "calendar_query":
        events = get_calendar_events(days_ahead=7)
        parts.append(format_events_for_speech(events))

    elif intent_name == "mail_query":
        emails = get_unread_emails(max_count=5)
        parts.append(format_emails_for_speech(emails))

    elif intent_name in ("note_read", "note_save"):
        notes = get_notes(search=query, limit=5)
        parts.append(format_notes_for_speech(notes))

    elif intent_name == "task_list":
        tasks = tracking.get_pending_tasks()
        if tasks:
            task_str = "; ".join(t["title"] for t in tasks[:5])
            parts.append(f"Pending tasks: {task_str}")
        else:
            parts.append("No pending tasks.")

    elif intent_name == "stats":
        parts.append(evolution.format_stats_for_speech())

    return "\n".join(parts)


async def process_utterance(
    text: str,
    convo: ConversationManager,
    ws: WebSocket,
) -> str:
    """Full pipeline: classify → gather context → generate response → dispatch actions."""
    start_t = time.time()

    intent = await classify_intent(text)
    intent_name = intent.get("intent", "conversation")
    entities = intent.get("entities", {})

    context = await build_context(intent, entities)
    system = convo.get_system_prompt(
        extra_context=(context + "\n\n" + ACTION_TAG_INSTRUCTIONS) if context else ACTION_TAG_INSTRUCTIONS
    )

    use_opus = intent_name in ("research", "plan") and intent.get("confidence", 0) > 0.7
    call_fn = call_claude_opus if use_opus else call_claude_haiku

    convo.add_user(text)
    messages = convo.get_messages()

    response = await call_fn(messages, system, max_tokens=500 if not use_opus else 1500)
    convo.add_assistant(response)

    evolution.record_interaction(intent_name)

    # Extract and dispatch action tags
    actions = ACTION_RE.findall(response)
    followup_parts = []
    for tag, value in actions:
        followup = await dispatch_action(tag, value, ws)
        if followup:
            followup_parts.append(followup)

    clean_response = ACTION_RE.sub("", response).strip()
    if followup_parts:
        clean_response = clean_response + " " + " ".join(followup_parts)

    clean_response = sanitize_for_tts(clean_response)
    elapsed = time.time() - start_t
    print(f"[JARVIS] Intent={intent_name} | {elapsed:.2f}s | {clean_response[:80]}")
    return clean_response


# ── WebSocket handler ─────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    convo = ConversationManager(user_name=USER_NAME)
    print(f"[JARVIS] Client connected.")

    # Send greeting
    greeting = f"Good {_time_of_day()}, {USER_NAME}. JARVIS online and ready."
    await _send_response(ws, greeting)

    # Check for proactive suggestions
    asyncio.create_task(_send_suggestions(ws, convo))

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                msg = {"type": "transcript", "text": raw, "final": True}

            msg_type = msg.get("type", "transcript")

            if msg_type == "transcript":
                text = msg.get("text", "").strip()
                final = msg.get("final", True)
                if not text or not final:
                    continue

                await ws.send_json({"type": "thinking"})

                try:
                    response_text = await process_utterance(text, convo, ws)
                except Exception as e:
                    print(f"[JARVIS] Error: {e}")
                    response_text = f"My apologies, {USER_NAME}. Something went sideways. Please try again."

                await _send_response(ws, response_text)

            elif msg_type == "ping":
                await ws.send_json({"type": "pong"})

            elif msg_type == "end_session":
                convo.end_session()
                break

    except WebSocketDisconnect:
        convo.end_session()
        print("[JARVIS] Client disconnected.")
    except Exception as e:
        print(f"[JARVIS] WebSocket error: {e}")
        convo.end_session()


async def _send_response(ws: WebSocket, text: str):
    """Send text response and TTS audio to client."""
    await ws.send_json({"type": "response", "text": text})
    if FISH_API_KEY:
        audio = await text_to_speech(text)
        if audio:
            await ws.send_bytes(audio)
        else:
            await ws.send_json({"type": "tts_fallback", "text": text})
    else:
        await ws.send_json({"type": "tts_fallback", "text": text})


async def _send_suggestions(ws: WebSocket, convo: ConversationManager):
    await asyncio.sleep(3)
    try:
        time_suggestions = get_time_based_suggestions()
        tasks = tracking.get_pending_tasks()
        task_suggestions = get_pending_task_suggestions(tasks)
        all_suggestions = time_suggestions + task_suggestions
        if all_suggestions:
            suggestion = all_suggestions[0]
            await _send_response(ws, suggestion)
    except Exception:
        pass


def _time_of_day() -> str:
    h = int(time.strftime("%H"))
    if 5 <= h < 12:
        return "morning"
    elif 12 <= h < 17:
        return "afternoon"
    elif 17 <= h < 21:
        return "evening"
    return "evening"


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    ssl_keyfile = "key.pem" if Path("key.pem").exists() else None
    ssl_certfile = "cert.pem" if Path("cert.pem").exists() else None

    print(f"[JARVIS] Starting on {HOST}:{PORT}")
    if ssl_keyfile:
        print("[JARVIS] SSL enabled (wss://)")
    else:
        print("[JARVIS] No SSL — using ws:// (fine for localhost)")

    uvicorn.run(
        "server:app",
        host=HOST,
        port=PORT,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        reload=False,
    )
