# J.A.R.V.I.S.

**Just A Rather Very Intelligent System** — a voice AI assistant you talk to from your phone, anywhere in the world. Works on 5G, T-Mobile hotspot, any WiFi, overseas — completely free.

---

## Use from Your Phone — Right Now (Free, Works Anywhere)

### Step 1 — Start JARVIS on your PC

```bash
cd jarvis
bash tunnel.sh
```

### Step 2 — It prints a URL like this:

```
  Your URL:  https://some-words.trycloudflare.com
```

### Step 3 — Open that URL in Safari on your iPhone

That's it. Tap the orb. Talk to JARVIS. It works from **anywhere** — T-Mobile 5G, home WiFi, work WiFi, overseas. No port forwarding. No router config. 100% free.

---

## First Time — Add Your API Keys

JARVIS needs two free API keys to think and speak:

| Key | Where to get it | Cost |
|-----|----------------|------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | Free tier |
| `FISH_API_KEY` | [fish.audio](https://fish.audio) → API Keys | Free tier |

**Easiest way to add them:** Open the JARVIS URL → tap `⋮` menu → Settings → paste keys there.

**Or edit `.env`:**
```bash
nano .env
# Set ANTHROPIC_API_KEY and FISH_API_KEY
```

---

## What JARVIS Can Do

- **Voice conversation** — talk naturally, JARVIS talks back with the MCU voice
- **Answer any question** — like ChatGPT but voice-first and hands-free
- **Build software** — "build me a landing page" → Claude Code does the work
- **Browse the web** — "search for the best restaurants near me"
- **Manage tasks** — "remind me to call someone tomorrow"
- **Remember things** — "I prefer dark mode" → it remembers forever
- **Control your Windows PC** (when it's on) — open apps, run commands
- **Audio-reactive orb** — Three.js particle visualization that pulses with voice

---

## How It Works

```
Your iPhone (anywhere) ──► Cloudflare Tunnel (free HTTPS) ──► JARVIS on your PC
                                                                      │
                                                            Claude AI + Fish TTS
```

- The tunnel gives you a real `https://` URL — required for mic access on iPhone
- Your PC runs the AI brain; your phone is just the interface
- When your PC is off, the tunnel stops (use a cloud server for 24/7 access)

---

## 24/7 Access (PC Off, Cloud Server)

Deploy to any free/cheap VPS (Oracle Free Tier is actually free forever):

```bash
git clone <repo> && cd jarvis
cp .env.example .env
nano .env   # Add API keys
bash tunnel.sh   # Or: docker compose up -d
```

Access from anywhere at the printed URL.

---

## Files

| File | What it does |
|------|-------------|
| `tunnel.sh` | **Start here** — launches JARVIS + free public tunnel |
| `run.sh` | Local-only start (same WiFi required) |
| `server.py` | Main server — AI, voice, WebSocket |
| `windows_agent.py` | Windows PC remote control |
| `frontend/` | iPhone/browser UI (pre-built in `dist/`) |
| `memory.py` | SQLite memory — JARVIS gets smarter over time |

---

## Environment Variables

Edit `.env` or use the Settings panel in the app:

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | Claude AI (free at console.anthropic.com) |
| `FISH_API_KEY` | ✅ | JARVIS voice (free at fish.audio) |
| `USER_NAME` | No | Your name |
| `FISH_VOICE_ID` | No | Voice model (defaults to JARVIS MCU voice) |
| `PORT` | No | Server port (default: 8340) |

---

## Windows PC Agent

Lets JARVIS control your PC remotely (open apps, run commands):

```powershell
pip install websockets psutil
python windows_agent.py --server wss://YOUR-TUNNEL-URL/ws/pc
```
