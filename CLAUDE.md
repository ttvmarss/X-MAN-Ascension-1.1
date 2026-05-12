# JARVIS — Windows 10 Edition

Just A Rather Very Intelligent System. Voice-first AI assistant built for Windows 10.

## What This Is

A voice AI assistant with a Three.js audio-reactive particle orb. You speak into your mic in Chrome, JARVIS responds with a British accent via Fish Audio TTS.

## Quick Start (Claude Code will handle this)

1. Run `setup_windows.bat` — installs all dependencies
2. Edit `.env` — add your Anthropic and Fish Audio API keys
3. Run `start_jarvis.bat` — launches server + opens Chrome
4. Click the page to activate, then speak

## Architecture

```
Chrome (Web Speech API) → WebSocket → FastAPI server.py → Claude Haiku → Fish Audio TTS → Chrome
                                            │
                                     Windows integrations:
                                     • Outlook COM (Calendar, Mail)
                                     • File-based Notes
                                     • Playwright (Web browsing)
                                     • Subprocess (Claude Code builds)
                                     • os.startfile (App launching)
```

## Files

| File | Purpose |
|------|---------|
| `server.py` | Main FastAPI WebSocket server |
| `frontend/src/orb.ts` | Three.js particle orb |
| `frontend/src/voice.ts` | Web Speech API + audio playback |
| `frontend/src/main.ts` | Frontend state machine |
| `memory.py` | SQLite FTS5 long-term memory |
| `calendar_access.py` | Outlook COM calendar (+ JSON fallback) |
| `mail_access.py` | Outlook COM email (read-only) |
| `notes_access.py` | File-based notes in ~/Documents/JARVIS Notes |
| `actions.py` | Windows actions: open URLs, apps, launch builds |
| `browser.py` | Playwright web automation |
| `conversation.py` | Three-tier conversation memory |
| `planner.py` | Multi-step task planning |
| `work_mode.py` | Claude Code session management |
| `screen.py` | Windows screen capture (PIL ImageGrab) |
| `tracking.py` | Task tracking with SQLite |

## Setup Requirements

- Python 3.11+
- Node.js 18+
- Google Chrome (required for Web Speech API)
- Anthropic API key: https://console.anthropic.com
- Fish Audio API key: https://fish.audio (optional — falls back to browser TTS)
- Microsoft Outlook (optional — for calendar/email integration)

## API Keys

Edit `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
FISH_API_KEY=...
USER_NAME=Tony
```

## Windows-Specific Notes

### Calendar & Mail
- If Microsoft Outlook is installed, JARVIS reads it via COM automation (no login needed)
- Without Outlook: calendar falls back to `~/Documents/JARVIS/calendar.json`; mail returns empty

### Voice
- Uses Chrome's built-in Web Speech API (no additional setup)
- TTS via Fish Audio API. Without a Fish API key, falls back to Windows built-in `speechSynthesis` (British George voice)

### App Launching
- Uses `os.startfile()` and `subprocess` — no AppleScript
- Claude Code builds run via PowerShell

### SSL
- Optional. Run `python generate_cert.py` for HTTPS/WSS
- Plain HTTP/WS works fine for localhost

## Running

**Backend only:**
```
python server.py
```

**Frontend dev mode (hot reload):**
```
cd frontend
npm run dev
```

**Full stack (one command):**
```
start_jarvis.bat
```

## Data Locations

- Memory DB: `~/Documents/JARVIS/memory.db`
- Tasks DB: `~/Documents/JARVIS/tasks.db`
- Notes: `~/Documents/JARVIS Notes/*.txt`
- Projects: `~/Documents/JARVIS Projects/`
- Preferences: `~/Documents/JARVIS/preferences.json`

## Troubleshooting

**"WebSocket connection failed"**
→ Make sure `python server.py` is running first

**"Microphone not working"**
→ Chrome must be the browser; allow mic permission when prompted

**"No voice output"**
→ Without Fish API key, uses Windows TTS. Say "hello JARVIS" to test

**"Calendar shows empty"**
→ Outlook not detected or not installed; add events to `~/Documents/JARVIS/calendar.json`

**Import errors**
→ Run `pip install -r requirements.txt` again; ensure you're using Python 3.11+
