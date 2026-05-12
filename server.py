"""
JARVIS Server — Windows 10 + iPhone Edition
FastAPI WebSocket backend: voice loop, tool-use dispatch, TTS, memory.
Now with: server-side STT (iOS), HTTPS auto-cert, LAN binding, Claude tool use.
"""
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Optional

import anthropic
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
FISH_API_KEY = os.getenv("FISH_API_KEY", "")
FISH_VOICE_ID = os.getenv("FISH_VOICE_ID", "3b554ef0ee6748e7a1bba6e6f87e4aea")
USER_NAME = os.getenv("USER_NAME", "sir")
HOST = os.getenv("HOST", "0.0.0.0")  # bind to LAN by default so phone can reach it
PORT = int(os.getenv("PORT", "8000"))
USE_HTTPS = os.getenv("USE_HTTPS", "auto").lower()  # auto | true | false

# ── Local modules ─────────────────────────────────────────────────────────────
import memory as mem_store
import tracking
import evolution
import learning
import transcription
import net_helper
from conversation import ConversationManager
from calendar_access import get_calendar_events, format_events_for_speech
from mail_access import get_unread_emails, format_emails_for_speech
from notes_access import save_note, get_notes, format_notes_for_speech
from actions import (
    open_url, open_browser, open_app,
    spawn_claude_code_build, do_research, connect_to_project,
)
from planner import generate_plan, format_plan_for_speech
from screen import get_screen_context
from suggestions import get_time_based_suggestions, get_pending_task_suggestions
from templates import JARVIS_SYSTEM_BASE
from qa import sanitize_for_tts
from tools_schema import JARVIS_TOOLS

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="JARVIS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
    return PlainTextResponse(
        "JARVIS backend is online.\n"
        "Build the frontend: cd frontend && npm run build\n"
        "Or run dev server:  cd frontend && npm run dev (then open http://localhost:8340)"
    )


@app.get("/manifest.json")
async def manifest():
    path = FRONTEND_DIST / "manifest.json"
    if path.exists():
        return FileResponse(str(path))
    return JSONResponse({"name": "JARVIS"})


@app.get("/sw.js")
async def service_worker():
    path = FRONTEND_DIST / "sw.js"
    if path.exists():
        return FileResponse(str(path), media_type="application/javascript")
    return PlainTextResponse("", media_type="application/javascript")


@app.get("/icon-192.svg")
async def icon_192():
    path = FRONTEND_DIST / "icon-192.svg"
    if path.exists():
        return FileResponse(str(path), media_type="image/svg+xml")
    return PlainTextResponse("not found", status_code=404)


@app.get("/icon-512.svg")
async def icon_512():
    path = FRONTEND_DIST / "icon-512.svg"
    if path.exists():
        return FileResponse(str(path), media_type="image/svg+xml")
    return PlainTextResponse("not found", status_code=404)


@app.get("/health")
async def health():
    return {
        "status": "online",
        "user": USER_NAME,
        "stt_available": transcription.is_available(),
        "tts_configured": bool(FISH_API_KEY),
    }


@app.post("/api/transcribe")
async def transcribe(request: Request):
    """Receive audio blob from iOS (or any client), return transcript."""
    body = await request.body()
    content_type = request.headers.get("content-type", "audio/webm")
    text = transcription.transcribe_audio(body, content_type=content_type)
    if text is None:
        return JSONResponse(
            {"error": "transcription unavailable", "text": ""},
            status_code=503,
        )
    return {"text": text}


# ── Anthropic client ──────────────────────────────────────────────────────────
_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def call_claude(messages: list[dict], system: str, use_tools: bool = True,
                       model: str = "claude-haiku-4-5-20251001", max_tokens: int = 600):
    """Run Claude with optional tool use. Returns the full message object."""
    loop = asyncio.get_event_loop()
    def _sync():
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if use_tools:
            kwargs["tools"] = JARVIS_TOOLS
        return _anthropic.messages.create(**kwargs)
    return await loop.run_in_executor(None, _sync)


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
            print(f"[TTS] Fish returned {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[TTS] Error: {e}")
    return None


# ── Tool dispatcher ───────────────────────────────────────────────────────────
async def dispatch_tool(name: str, args: dict, ws: WebSocket) -> str:
    """Execute a tool call. Returns a short user-facing follow-up message."""
    try:
        if name == "build_project":
            desc = args.get("description", "")
            task_id = spawn_claude_code_build(desc, args.get("project_name"))
            evolution.record_interaction("build")
            await ws.send_json({"type": "action", "action": "build_started", "task_id": task_id})
            return f"Building {desc[:60]}. I'll notify you when it's done, {USER_NAME}."

        if name == "browse_web":
            open_browser(args.get("query_or_url", ""))
            evolution.record_interaction("browse")
            return ""

        if name == "research_topic":
            topic = args.get("topic", "")
            task_id = do_research(topic)
            evolution.record_interaction("research")
            await ws.send_json({"type": "action", "action": "research_started", "task_id": task_id})
            return f"Researching {topic[:60]}. Report will be ready shortly."

        if name == "add_task":
            title = args.get("title", "")
            priority = int(args.get("priority", 3))
            due_in_hours = args.get("due_in_hours")
            due_at = time.time() + float(due_in_hours) * 3600 if due_in_hours else None
            tracking.add_task(title, priority=priority, due_at=due_at)
            evolution.record_interaction("task")
            return ""

        if name == "remember":
            fact = args.get("fact", "")
            category = args.get("category", "general")
            mem_store.save_memory(fact, category=category, importance=7)
            learning.set_preference(fact.split(":")[0].strip()[:40], fact)
            return ""

        if name == "save_note":
            save_note(args.get("content", ""), title=args.get("title", ""))
            evolution.record_interaction("notes")
            return ""

        if name == "make_plan":
            plan = generate_plan(args.get("goal", ""))
            return format_plan_for_speech(plan)

        if name == "open_app_or_url":
            target = args.get("target", "")
            if target.startswith("http"):
                open_url(target)
            else:
                open_app(target)
            evolution.record_interaction("open")
            return ""

        if name == "connect_to_project":
            path = args.get("project_path", "")
            connect_to_project(path)
            evolution.record_interaction("project")
            return f"Opened Claude Code in {path}."
    except Exception as e:
        print(f"[TOOL] {name} failed: {e}")
        return f"Tool {name} failed: {e}"

    return ""


# ── Context gathering ─────────────────────────────────────────────────────────
def build_context() -> str:
    """Gather lightweight context attached to every turn."""
    parts = []
    screen = get_screen_context()
    if screen:
        parts.append(screen)
    prefs = learning.format_preferences_for_context()
    if prefs:
        parts.append(prefs)
    return "\n".join(parts)


def maybe_inject_data(user_text: str) -> str:
    """Detect data-fetching intents and inline the data. Cheap heuristic."""
    text = user_text.lower()
    parts = []

    if any(k in text for k in ["calendar", "schedule", "meeting", "appointment", "today's plan"]):
        events = get_calendar_events(days_ahead=7)
        parts.append("Calendar: " + format_events_for_speech(events))

    if any(k in text for k in ["email", "mail", "inbox", "unread"]):
        emails = get_unread_emails(max_count=5)
        parts.append("Mail: " + format_emails_for_speech(emails))

    if any(k in text for k in ["note", "notes"]):
        notes = get_notes(limit=5)
        if notes:
            parts.append("Notes: " + format_notes_for_speech(notes))

    if any(k in text for k in ["task", "tasks", "to-do", "todo", "pending"]):
        tasks = tracking.get_pending_tasks()
        if tasks:
            parts.append("Tasks: " + "; ".join(t["title"] for t in tasks[:5]))

    if any(k in text for k in ["remember", "recall", "what do you know"]):
        mems = mem_store.search_memories(user_text, limit=5)
        if mems:
            parts.append("Memories: " + " | ".join(m["content"] for m in mems))

    return "\n".join(parts)


# ── Core pipeline ─────────────────────────────────────────────────────────────
async def process_utterance(text: str, convo: ConversationManager, ws: WebSocket) -> str:
    start_t = time.time()

    context_parts = [build_context()]
    data_ctx = maybe_inject_data(text)
    if data_ctx:
        context_parts.append("Live data:\n" + data_ctx)

    system = convo.get_system_prompt(extra_context="\n\n".join(p for p in context_parts if p))

    convo.add_user(text)
    messages = convo.get_messages()

    # Tool-use loop: Claude may call a tool, we execute, feed result back
    final_text_parts = []
    followups = []
    iterations = 0

    while iterations < 3:
        iterations += 1
        response = await call_claude(messages, system, use_tools=True)

        text_blocks = []
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text_blocks.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        if text_blocks:
            final_text_parts.extend(text_blocks)

        if response.stop_reason != "tool_use" or not tool_calls:
            break

        # Append assistant message with tool calls, then tool results
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tc in tool_calls:
            followup = await dispatch_tool(tc.name, tc.input, ws)
            if followup:
                followups.append(followup)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": followup or "Done.",
            })
        messages.append({"role": "user", "content": tool_results})

    final_text = " ".join(final_text_parts).strip()
    if followups:
        final_text = (final_text + " " + " ".join(followups)).strip()
    if not final_text:
        final_text = "Done, sir."

    final_text = sanitize_for_tts(final_text)
    convo.add_assistant(final_text)

    evolution.record_interaction("conversation")
    print(f"[JARVIS] {time.time()-start_t:.2f}s | {final_text[:100]}")
    return final_text


# ── WebSocket handler ─────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    convo = ConversationManager(user_name=USER_NAME)
    print("[JARVIS] Client connected.")

    # Greeting
    greeting = f"Good {_time_of_day()}, {USER_NAME}. JARVIS online."
    await _send_response(ws, greeting)

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
                text = (msg.get("text") or "").strip()
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
    await ws.send_json({"type": "response", "text": text})
    if FISH_API_KEY:
        audio = await text_to_speech(text)
        if audio:
            await ws.send_bytes(audio)
            return
    await ws.send_json({"type": "tts_fallback", "text": text})


async def _send_suggestions(ws: WebSocket, convo: ConversationManager):
    await asyncio.sleep(4)
    try:
        suggestions = get_time_based_suggestions()
        suggestions += get_pending_task_suggestions(tracking.get_pending_tasks())
        if suggestions:
            await _send_response(ws, suggestions[0])
    except Exception:
        pass


def _time_of_day() -> str:
    h = int(time.strftime("%H"))
    if 5 <= h < 12:
        return "morning"
    if 12 <= h < 17:
        return "afternoon"
    return "evening"


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    # HTTPS auto-setup
    https_ok = False
    if USE_HTTPS in ("auto", "true"):
        https_ok = net_helper.ensure_self_signed_cert("cert.pem", "key.pem")
    if USE_HTTPS == "false":
        https_ok = False

    ssl_keyfile = "key.pem" if https_ok else None
    ssl_certfile = "cert.pem" if https_ok else None

    net_helper.print_connection_banner(HOST, PORT, https=https_ok)

    uvicorn.run(
        "server:app",
        host=HOST,
        port=PORT,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        reload=False,
        log_level="warning",
    )
