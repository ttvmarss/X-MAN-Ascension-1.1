# Tooling Inventory — Everything Needed to Build It

Derived from the free Blueprint readiness checklist, kit requirements, and `/how-to-build-your-own-jarvis`.

## A. Hardware & OS

| Item | Requirement |
|------|-------------|
| OS | Windows 11 (primary target for Creator/Founder kits) |
| GPU | NVIDIA CUDA, **8 GB+ VRAM** for full-speed cloned voice (XTTS); less VRAM → slower or Windows TTS fallback |
| Mic + speakers | Tested in Windows sound settings |
| Disk | Local folder only — **not** cloud-synced |

Starter Kit path: any Windows PC, **no GPU** (browser Web Speech TTS/STT).

## B. Core install (Builder machine)

| Tool | Why | Get it |
|------|-----|--------|
| **Python 3.10 or 3.11** | Runtime for Flask backend + voice/ML | python.org |
| **Git** | Project + model repos | git-scm.com |
| **Google Chrome** | Browser automation target | google.com/chrome |
| **Claude Code CLI** | Generates the project from Blueprint prompts | Anthropic Claude Code docs |
| **NVIDIA drivers + CUDA** | XTTS / Whisper GPU acceleration | NVIDIA |

## C. AI brain (runtime — paid, separate from kits)

| Service | Role | Notes |
|---------|------|-------|
| **Anthropic API key** | Claude = reasoning / tool calling | Required at runtime; billed per token |
| **Claude Pro (~$20/mo)** | Used while *building* with Claude Code | Called out on `/get-access` |
| Optional brains (Starter) | ChatGPT / OpenRouter | Kit claims multi-provider for Starter |

Two-model pattern (Blueprint): strong model for speech; cheap model for background parsing/summaries; large personality + tool schema as **cached** prompt blocks.

## D. Voice I/O (local)

| Tool | Role | Notes |
|------|------|-------|
| **OpenAI Whisper** (local) | Speech-to-text | “Whisper-style” STT; local, free after download |
| **Coqui XTTS** | Text-to-speech + **voice cloning** | Named in Blueprint license/attribution |
| Windows voice fallback | TTS without GPU | Creator Kit “one-click Windows-voice fallback” |
| Wake word **"JARVIS"** | Hands-free activation | Local speech recognition (Creator+) |

## E. Memory stack

| Tool | Role |
|------|------|
| **ChromaDB** | Vector / semantic memory |
| **SQLite** | Conversation history |
| **Markdown vault** | Human-readable saved knowledge |

## F. Backend & UI libraries (named / implied)

| Tool | Role |
|------|------|
| **Flask** | HTTP app shell |
| **Flask-SocketIO** (Socket.IO) | Real-time UI ↔ backend |
| Browser frontend | Orb HUD + chat + telemetry (Three.js-style particle orb on marketing site; kit ships holographic UI) |
| **Python tool dispatcher** | ~50 functions behind a JSON schema the brain can call |

## G. Automation / “skills” targets (Creator Kit feature list)

Wire tools that talk to these systems (you bring accounts/apps):

| Domain | Integrations named publicly |
|--------|----------------------------|
| Desktop | Open/close apps, window automation, files |
| Office | Word, Excel |
| Browser | Drive Chrome for search / navigate / act |
| Info | Weather, news, web search, **WolframAlpha** |
| Personal | Reminders, calendar, **Outlook** email |
| Media | **Spotify** |
| System | System status / telemetry |
| Security | Background security monitor |

## H. Accounts & API keys checklist

Create / save privately:

- [ ] Anthropic API key (runtime brain)
- [ ] Claude Pro / Claude Code login (build-time)
- [ ] Optional: OpenAI or OpenRouter (Starter multi-brain)
- [ ] Optional: WolframAlpha App ID
- [ ] Optional: weather API (if not scraped)
- [ ] Optional: Spotify developer app
- [ ] Outlook / Microsoft account for mail/calendar tools
- [ ] Stripe is **only** for buying ManinaLabs kits — not needed to run an assistant

## I. Marketing-site tech (only if cloning the *landing page*)

Not required for the assistant itself:

- Static hosting (S3 + CloudFront pattern)
- Stripe Checkout + Cognito OTP vault
- Three.js particle hero
- Space Grotesk / Space Mono fonts

## J. Recommended open alternatives (if not buying Creator voice)

| Need | ManinaLabs path | Practical open alternatives |
|------|-----------------|----------------------------|
| TTS / clone | Coqui XTTS (+ their trained voice in Creator) | Coqui XTTS (self-train), Piper, Edge-TTS, Fish Audio, ElevenLabs |
| STT | Whisper | faster-whisper, Whisper.cpp, Web Speech API |
| Wake word | Local “JARVIS” | openWakeWord, Picovoice Porcupine, Sherpa-ONNX KWS |
| Brain | Claude API | Claude, GPT, Groq, Ollama (local) |
| Orchestration | Flask + Socket.IO | FastAPI + WebSockets (already in this repo’s JARVIS branches) |
| Memory | Chroma + SQLite | Chroma, LanceDB, SQLite FTS, markdown notes |
| Browser tools | Chrome automation | Playwright / Selenium |
| Desktop control | Windows automation | `pywinauto`, PowerShell, Win32 |

## K. Cost picture (honest, from public copy)

| Cost | Who pays |
|------|----------|
| Kit purchase ($29–$999) | Optional — educational assets from ManinaLabs |
| Claude Pro ~$20/mo | Builder (while using Claude Code) |
| Anthropic API tokens | Ongoing runtime |
| GPU electricity / hardware | You |
| Third-party APIs (Wolfram, Spotify, etc.) | You |
