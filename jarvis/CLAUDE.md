# JARVIS — Voice AI Assistant

## Overview
JARVIS (Just A Rather Very Intelligent System) is a cloud-based voice AI assistant accessible from anywhere — iPhone, PC, or any browser — even when your home PC is off. It runs on a cloud server 24/7, processes voice commands, can control your Windows PC remotely when it's online, and responds with natural speech.

---

## Quick Start (Cloud Server)

### 1. Clone and set up
```bash
git clone <repo>
cd jarvis
bash setup.sh       # Installs all dependencies and builds the frontend
```

### 2. Configure API keys
```bash
cp .env.example .env
nano .env           # Add ANTHROPIC_API_KEY and FISH_API_KEY
```

### 3. Start JARVIS
```bash
bash start.sh
```

### 4. Access from anywhere
- **Browser**: `http://YOUR-SERVER-IP:8340`
- **iPhone**: Open the same URL in Safari or Chrome
- **PC**: Connect the Windows agent (see below)

---

## Cloud Deployment (Recommended — works from iPhone/5G/anywhere)

Deploy to any VPS (DigitalOcean, AWS, Google Cloud, Oracle Free Tier, etc.):

```bash
# On your cloud server:
git clone <repo> && cd jarvis
cp .env.example .env
nano .env              # Add your API keys + AUTH_TOKEN for security

docker compose up -d   # Runs JARVIS 24/7, auto-restarts on crash
```

Access at: `http://YOUR-VPS-IP:8340`

For HTTPS (recommended for production):
- Put Nginx in front with a Let's Encrypt cert
- Or use Cloudflare Tunnel for zero-config HTTPS

---

## Windows PC Agent

Lets JARVIS control your Windows PC remotely (open apps, run commands, etc.).
The PC agent connects TO the cloud server — so JARVIS works even when your PC is off.
When the PC is off, PC-specific commands are queued or gracefully reported as unavailable.

**On your Windows PC:**
```powershell
pip install websockets psutil
python windows_agent.py --server wss://YOUR-SERVER:8340 --token YOUR_AUTH_TOKEN
```

Or as a background service:
```powershell
# Run at startup — add to Task Scheduler
pythonw windows_agent.py --server wss://YOUR-SERVER:8340 --token YOUR_AUTH_TOKEN
```

---

## iPhone / Mobile Access

No app install needed. JARVIS is a web app:
1. Open Safari or Chrome on your iPhone
2. Go to `http://YOUR-SERVER-IP:8340`
3. **Add to Home Screen** (Share → Add to Home Screen) for an app-like experience
4. Tap the orb, speak to JARVIS
5. Works on 5G, LTE, Wi-Fi — from anywhere in the world

**Note**: Web Speech API (voice recognition) requires Chrome on Android or Safari on iOS.

---

## Architecture

```
iPhone / Browser ──────────────────────────────────┐
                                                   ↓
                              ┌─────────────────────────────┐
                              │   JARVIS Cloud Server       │
                              │   (FastAPI + WebSocket)     │
                              │                             │
                              │  • Claude Haiku (voice AI)  │
                              │  • Fish Audio TTS           │
                              │  • Web browsing (Playwright)│
                              │  • Memory (SQLite)          │
                              │  • Task planning            │
                              └─────────────────────────────┘
                                         ↕ WebSocket (/ws/pc)
                              ┌─────────────────────────────┐
                              │   Windows PC Agent          │
                              │   (windows_agent.py)        │
                              │  • Open apps                │
                              │  • Run commands             │
                              │  • System monitoring        │
                              │  • File management          │
                              └─────────────────────────────┘
```

---

## Key Files

| File | Purpose |
|------|---------|
| `server.py` | Main server — WebSocket, LLM, TTS, actions |
| `windows_agent.py` | Windows PC remote control agent |
| `frontend/src/main.ts` | Frontend state machine + UI |
| `frontend/src/voice.ts` | Speech recognition + audio playback |
| `frontend/src/orb.ts` | Three.js particle visualization |
| `memory.py` | SQLite memory system with FTS5 |
| `actions.py` | System actions (terminal, browser, Claude Code) |
| `browser.py` | Playwright web automation |
| `work_mode.py` | Persistent Claude Code sessions |
| `planner.py` | Multi-step task planning |
| `Dockerfile` | Container for cloud deployment |
| `docker-compose.yml` | One-command cloud deployment |
| `setup.sh` | First-time setup script |
| `start.sh` | Start the server |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | Claude API access (console.anthropic.com) |
| `FISH_API_KEY` | ✅ | Fish Audio TTS (fish.audio) |
| `FISH_VOICE_ID` | No | Voice model ID (defaults to JARVIS MCU) |
| `USER_NAME` | No | Your name for JARVIS to use |
| `AUTH_TOKEN` | No | Require token auth for remote access |
| `WEATHER_LOCATION` | No | Your city (blank = auto-detect) |
| `CALENDAR_ACCOUNTS` | No | Apple Calendar emails (macOS only) |
| `PORT` | No | Server port (default: 8340) |
| `JARVIS_SERVER` | No | Cloud server URL (Windows agent only) |

---

## WebSocket Protocol

**Client → Server:**
```json
{"type": "transcript", "text": "open Chrome", "isFinal": true}
{"type": "fix_self"}
{"type": "stop_audio"}
```

**Server → Client:**
```json
{"type": "audio", "data": "<base64 mp3>", "text": "spoken text"}
{"type": "status", "state": "thinking|speaking|idle|working"}
{"type": "stop_audio"}
{"type": "task_spawned", "task_id": "...", "prompt": "..."}
{"type": "task_complete", "task_id": "...", "status": "...", "summary": "..."}
{"type": "pc_result", "result": {...}}
```

**PC Agent → Server (`/ws/pc`):**
```json
{"type": "agent_hello", "agent": "windows", "system": {...}}
{"type": "pc_result", "command_id": "...", "result": {...}}
```

---

## Action Tags (in LLM responses)

| Tag | Effect |
|-----|--------|
| `[ACTION:BUILD] description` | Spawn Claude Code to build a project |
| `[ACTION:BROWSE] url` | Open URL in browser |
| `[ACTION:RESEARCH] brief` | Deep web research with Playwright |
| `[ACTION:PROMPT_PROJECT] name \|\|\| prompt` | Connect to existing project |
| `[ACTION:SCREEN]` | Capture and describe screen (macOS) |
| `[ACTION:OPEN_TERMINAL]` | Open terminal with Claude Code |
| `[ACTION:ADD_TASK] priority \|\|\| title \|\|\| desc \|\|\| due` | Create task |
| `[ACTION:REMEMBER] content` | Store fact in memory |
| `[ACTION:CREATE_NOTE] title \|\|\| body` | Create Apple Note (macOS) |

---

## Conventions

- JARVIS personality: British butler, dry wit, economy of language
- Max 1-2 sentences per voice response — never 3
- No markdown in voice responses
- Action tags at end of response (don't count toward sentence limit)
- SQLite for all local data storage (`data/` directory)
- macOS integrations (Calendar, Mail, Notes, AppleScript) fail gracefully on Linux/cloud
