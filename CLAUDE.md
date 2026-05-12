# JARVIS — Windows 10 + iPhone Edition

Just A Rather Very Intelligent System. Voice-first AI assistant.
Runs on a Windows 10 PC, callable from your iPhone (or any phone) on the same WiFi.

## What it does

- Voice conversation (continuous on PC, push-to-talk on phone)
- Reads your Outlook calendar and unread email (Windows Outlook COM)
- Saves notes and remembers preferences across sessions
- Builds software via Claude Code subprocess
- Browses the web, opens apps, plans tasks
- Audio-reactive Three.js particle orb UI

## Setup (Windows 10 PC)

1. **Run** `setup_windows.bat`
   Installs Python deps, Whisper STT model, Playwright, frontend, builds the UI.
2. **Edit** `.env` — add your Anthropic API key. Fish Audio key is optional (falls back to Windows/iOS built-in voice).
3. **Run** `start_jarvis.bat`
   Server starts, prints a QR code with your LAN URL.

That's it. Open the URL on your PC, or scan the QR with your iPhone.

## iPhone usage

1. Make sure your iPhone is on the **same WiFi** as the PC.
2. Scan the QR code printed in the JARVIS console (or type the LAN URL in Safari).
3. Safari will warn about the self-signed certificate — tap **Show Details → Visit Website → Continue**. (It's your own cert generated locally; nobody else can use it.)
4. Tap **Tap to activate JARVIS** → allow microphone permission.
5. **Hold** the big mic button to talk, **release** to send. JARVIS responds with voice.
6. Optional: **Share → Add to Home Screen** to install JARVIS as a PWA. It launches like a native app.

### Why push-to-talk on iPhone?

iOS Safari's continuous speech recognition is unreliable. JARVIS records audio on your phone, sends it to the PC, and transcribes it locally using `faster-whisper`. Your audio never leaves your network.

## How it works

```
PC microphone (Chrome)  ─┐
                          ├─► WebSocket ─► server.py ─► Claude (tool use)
iPhone mic (Safari) ─────┘                                  │
   audio blob → /api/transcribe → Whisper → text           │
                                                            ▼
Claude tool call → dispatch (build / browse / remember / ...)
   │
   ▼
Response text → Fish Audio TTS → mp3 → WebSocket → playback
```

## File layout

| File | Purpose |
|------|---------|
| `server.py` | FastAPI WebSocket server, Claude tool-use dispatch, HTTPS auto-setup |
| `transcription.py` | faster-whisper STT for iOS/Safari clients |
| `net_helper.py` | LAN IP detection, self-signed cert, QR code printing |
| `tools_schema.py` | Anthropic tool-use schema for all JARVIS actions |
| `frontend/src/orb.ts` | Three.js audio-reactive particle orb |
| `frontend/src/voice.ts` | Dual-mode voice: Web Speech API (PC) + MediaRecorder (iOS) |
| `frontend/src/main.ts` | State machine, WebSocket client, PWA |
| `memory.py` | SQLite FTS5 long-term memory |
| `conversation.py` | Three-tier conversation memory (buffer + summary + long-term) |
| `calendar_access.py` | Outlook COM calendar + JSON fallback |
| `mail_access.py` | Outlook COM email (read-only) |
| `notes_access.py` | File-based notes in `~/Documents/JARVIS Notes` |
| `actions.py` | Windows actions: launch apps, URLs, Claude Code builds |
| `browser.py` | Playwright web automation |
| `planner.py` | Multi-step task planning |
| `work_mode.py` | Persistent Claude Code session management |
| `screen.py` | Active window awareness via win32gui |
| `tracking.py` | Task tracking SQLite DB |
| `suggestions.py` | Proactive time-based suggestions |
| `learning.py` | Preference tracking |
| `evolution.py` | Usage stats |

## Configuration (`.env`)

```bash
ANTHROPIC_API_KEY=sk-ant-...        # required
FISH_API_KEY=...                     # optional — uses browser TTS if missing
USER_NAME=Tony                       # what JARVIS calls you
HOST=0.0.0.0                         # bind LAN (0.0.0.0) or localhost only
PORT=8000
USE_HTTPS=auto                       # auto generates cert; "false" for plain HTTP
WHISPER_MODEL=base.en                # tiny.en / base.en / small.en / medium.en
```

## Tool-use actions

Claude returns structured tool calls (no more regex parsing). Available tools:

- `build_project` — spawn Claude Code subprocess
- `browse_web` — open URL or search query in default browser
- `research_topic` — deep research with HTML report output
- `add_task` — track a task with priority + optional due time
- `remember` — store fact/preference for future sessions
- `save_note` — create a longer note in `~/Documents/JARVIS Notes`
- `make_plan` — multi-step plan generation
- `open_app_or_url` — launch a Windows app or URL
- `connect_to_project` — open Claude Code in an existing directory

## Voice modes

| Device | Mode | Why |
|--------|------|-----|
| Windows + Chrome | Continuous (Web Speech API) | Best UX, hands-free |
| iPhone + Safari | Push-to-talk (MediaRecorder → Whisper) | iOS Safari can't do reliable continuous STT |
| Android + Chrome | Continuous | Web Speech API works |
| Mac + Safari | Push-to-talk | Same iOS Safari limitation |

The frontend auto-detects which mode to use.

## TTS

- **Primary**: Fish Audio API → cinematic JARVIS voice
- **Fallback**: Browser `speechSynthesis` API
  - Windows: George (British)
  - iOS: Daniel (British)

## Troubleshooting

**Phone can't connect**
- Check the iPhone is on the same WiFi as the PC
- Windows Firewall: allow Python through Private networks
- If you see "connection refused", the server isn't running — check the JARVIS Backend window

**iPhone says "site is not secure"**
- Expected. Tap "Show Details → Visit Website". The cert is self-signed.

**No transcription on iPhone**
- First request loads the Whisper model (5-10s on first use)
- Check the console for "[STT] Whisper ready."
- If faster-whisper failed to install, reinstall: `pip install faster-whisper`

**No voice output**
- Without Fish API key, uses built-in TTS (Windows George, iOS Daniel)
- Make sure your phone isn't on silent mode

**Calendar/email empty**
- Outlook not detected. Either install Outlook, or add events to `~/Documents/JARVIS/calendar.json`

## Data locations

- Memory DB: `~/Documents/JARVIS/memory.db`
- Tasks DB: `~/Documents/JARVIS/tasks.db`
- Notes: `~/Documents/JARVIS Notes/*.txt`
- Built projects: `~/Documents/JARVIS Projects/`
- SSL certs: `cert.pem` + `key.pem` in repo root (auto-generated, gitignored)
