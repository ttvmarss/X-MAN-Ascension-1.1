# Architecture — Target System (Public Blueprint)

Source: ManinaLabs *Build Your Own J.A.R.V.I.S. — The Complete Builder Blueprint* v2.0 **free preview** (Chapter 1 + front matter), plus `/how-to-build-your-own-jarvis` and kit feature lists.

## High-level diagram

```
Browser UI (orb · HUD · chat)
        │ websocket
        ▼
Flask + Socket.IO backend (app.py)
  turn handler · speech loop · brain caller · dispatch
        │
   ┌────┼────────────────────────────┐
   ▼    ▼              ▼             ▼
MEMORY  TOOLS       VOICE I/O     MONITORS
Chroma  ~50 fns     XTTS speak    daemon loops
SQLite  dispatcher  Whisper listen
Markdown vault
        │
        ▼
   Anthropic Claude API (cloud brain)
```

## Six subsystems

| # | Subsystem | Role | Named modules (preview) |
|---|-----------|------|-------------------------|
| 1 | Core brain | Claude API, streaming, tool decisions, two-model split | brain caller in `app.py` |
| 2 | Voice pipeline | Mic → Whisper STT; reply → XTTS cloned voice (separate subprocess) | `xtts_server.py`, `jarvis_voice.py` |
| 3 | Memory | SQLite history + Chroma vectors + markdown vault | `jarvis_memory.py` |
| 4 | Tools | ~50 callable functions + schema + dispatcher | `jarvis_tools.py` |
| 5 | UI | Particle orb, telemetry, chat; standby / awake / workspace modes | `templates/index.html`, `static/v2/` |
| 6 | Automation | Security, health, clipboard/file watchers, weather, telemetry | `jarvis_monitors.py` |

Shared state lives in `jarvis_state.py` — **import-graph leaf** (imports none of the feature modules).

## One conversational turn

1. Wake / speak (“JARVIS, what’s the weather?”)
2. Mic capture → speech loop (end-of-utterance)
3. Whisper → text
4. Memory retrieval prepended to context
5. Claude streams reply (may call tools mid-turn)
6. Tool dispatcher runs, results fed back
7. Sentence streamer → XTTS → speakers (start talking before full reply finishes)
8. Orb reacts; chat updates; turn saved to memory

## Design principles (from Blueprint)

1. **Modular** — single-purpose modules; shared state is a leaf
2. **Stream everything** — speak sentences as they complete (~1–2s sooner)
3. **Two-model split** — strong model for spoken replies; cheap/fast for background
4. **Personality = cached system prompt** — character + reference lines, prompt-cached
5. **Fail soft** — dead tool / voice / monitor must not kill the process

## Build methodology

- Project is generated with **Claude Code** (vibe-coding) using engineered prompts from the Blueprint
- Twelve build phases with milestones (full book); free preview covers architecture only
- Local project folder must **not** be inside OneDrive / Dropbox / Google Drive (corrupts model downloads)

## Explicitly out of scope (Blueprint “Excluded Features”)

Camera vision, engineering/CAD agents, meeting integration, multi-hour academic research, production cloud infrastructure — Sam’s *personal* demos (Fusion 360, 3D print, companion phone app) go beyond the kit core.
