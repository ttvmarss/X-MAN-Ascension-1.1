# JARVIS — Node.js Edition (Windows 10 + iPhone)

Voice-first AI assistant. **Pure Node.js + browser** — no Python required.
Free high-quality JARVIS voice using Microsoft Edge's neural voices (no API key).

## What you get

- Hands-free voice conversation on your Windows 10 PC
- The same app on your iPhone over local WiFi (push-to-talk)
- A British-voiced AI that calls you "sir"
- An audio-reactive Three.js orb that looks like the MCU JARVIS
- Real actions: open apps, browse the web, build software via Claude Code, remember things, manage tasks
- 100% free voice — Microsoft Edge neural TTS, no API key, no quota
- Anthropic Claude API key required (pay-as-you-go from Anthropic; not from us)

## Setup — Windows 10

1. Install **Node.js 18+** from <https://nodejs.org> (LTS recommended)
2. Run `setup_windows.bat` — installs deps and builds the frontend
3. Edit `.env` — paste your Anthropic API key from <https://console.anthropic.com>
4. Run `start_jarvis.bat`
5. Open the URL it prints (looks like `https://localhost:8000`) in Chrome or Edge
6. Click anywhere → allow microphone → start speaking

## Use it on your iPhone

1. Make sure your iPhone is on the same WiFi as your PC
2. Look at the QR code in the JARVIS console window — scan it with your phone camera
3. Safari opens → it will warn about the certificate (it's self-signed, that's fine)
   → tap **Show Details → Visit Website → Continue**
4. Tap **Tap to activate JARVIS** → allow microphone permission
5. **Hold the big mic button** to talk, **release** to send
6. Optional: Safari → Share → **Add to Home Screen**. JARVIS launches like a native app.

> Windows Firewall: on first start, Windows may ask whether to allow Node.js
> through the firewall. Click **Allow access** for **Private networks** so
> your phone can reach the server.

## How it works

```
PC mic / phone mic ──► browser ──► WebSocket ──► server.js
                                                    │
                                                    ▼
                                            Claude (tool use)
                                                    │
                              ┌─────────────────────┼──────────────┐
                              ▼                     ▼              ▼
                         remember          open browser       build_project
                         add_task          open app           save_note
                                                              get_time
                                                    │
                                                    ▼
                                  MS Edge neural TTS (free)
                                                    │
                                                    ▼
                                          MP3 audio back to browser
```

## File layout

```
server.js              ← main entry: Express + WebSocket + HTTPS
package.json
src/
├── claude.js          ← Anthropic SDK + tool-use loop
├── tools.js           ← Tool schema definitions
├── actions.js         ← Windows actions: launch apps, open URLs, spawn builds
├── tts.js             ← FREE MS Edge neural TTS (JARVIS voice)
├── transcribe.js      ← Optional Whisper for iOS server-side STT
├── memory.js          ← SQLite long-term memory + tasks
├── conversation.js    ← Three-tier conversation memory
└── net.js             ← LAN IP, SSL cert, QR-code banner
frontend/              ← Vite + TypeScript + Three.js orb UI
```

## Voice options

Edit `JARVIS_VOICE` in `.env`:

| Voice | Description |
|-------|-------------|
| `en-GB-RyanNeural` | **Default.** British male, calm, intelligent — JARVIS-like |
| `en-GB-ThomasNeural` | Alternative British male |
| `en-US-GuyNeural` | American male |
| `en-US-TonyNeural` | American male, deeper |
| `en-GB-SoniaNeural` | British female |

All free, all run through Microsoft Edge's public TTS endpoint.

## Tools (what JARVIS can actually do)

| Tool | Trigger phrase examples |
|------|------------------------|
| `remember` | "Remember that I prefer React over Vue" |
| `recall` | "What do you remember about my project?" |
| `add_task` | "Add a task to call the dentist tomorrow" |
| `list_tasks` | "What's on my to-do list?" |
| `browse_web` | "Search for the best pizza in Austin" |
| `open_app` | "Open Notepad" / "Launch Spotify" |
| `build_project` | "Build me a landing page for my band" |
| `save_note` | "Save a note: meeting at 3pm tomorrow" |
| `get_time` | "What time is it?" / "What's today's date?" |

`build_project` and `connect_to_project` require **Claude Code CLI** on your
PATH. Install it from <https://claude.ai/code>.

## Data locations

- Memory + tasks DB: `~/Documents/JARVIS/memory.db`
- Notes: `~/Documents/JARVIS Notes/*.txt`
- Projects built by JARVIS: `~/Documents/JARVIS Projects/`
- Self-signed SSL: `cert.pem` + `key.pem` in the repo root (auto-generated, gitignored)

## iOS speech-to-text (optional)

By default, iPhone uses Safari's `webkitSpeechRecognition` — works on iOS 14.5+.

For more reliable transcription, install Whisper:
```
npm install nodejs-whisper
```
First request downloads a ~150 MB model. After that, iOS audio is transcribed
locally on your PC (never leaves your network).

## Troubleshooting

**"Cannot find module 'better-sqlite3'"**
→ Native module didn't build. Make sure you have a C++ toolchain. On Windows:
```
npm install --global windows-build-tools
```
Or just install Visual Studio Build Tools with C++ workload.

**Phone can't connect**
- Same WiFi? Check.
- Windows Firewall: allow Node.js for Private networks
- Try the LAN URL (e.g. `https://192.168.x.x:8000`) instead of the QR

**iPhone says "not secure"** — expected. Tap Show Details → Visit Website. The
cert is your own, generated locally, valid for 5 years.

**No JARVIS voice (only text)** — first synthesis takes ~2 seconds (MS Edge
TTS connects via WebSocket). If it consistently fails, check your firewall
isn't blocking outbound 443 from Node.

**Microphone won't activate** — Chrome/Safari require HTTPS for mic permission
on non-localhost. The auto-generated cert covers this; just accept the warning
the first time.
