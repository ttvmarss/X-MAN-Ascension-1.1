# What’s Free From ManinaLabs (Honest Inventory)

Goal: rebuild a JARVIS-class assistant **without buying** kits.  
Audited: 2026-08-24 against [jarvis.driftworksstudios.com](https://jarvis.driftworksstudios.com).

## Short answer

| Want | Free? | Where |
|------|-------|-------|
| Full 119-page Blueprint | **No** — $29 | `/get-access` product `blueprint` |
| Starter / Creator / Founder source kits | **No** — $79–$999 | paid downloads after Stripe |
| His trained voice model | **No** — Creator+ only | paid |
| Copy-paste Claude Code prompts (Ch.2+) | **No** | paid Blueprint |
| **Blueprint free preview (Ch.1 + TOC)** | **Yes** | [PDF](https://jarvis.driftworksstudios.com/assets/jarvis-blueprint-preview.pdf) · archived in [`free/`](./free/) |
| **How-to-build web guide** | **Yes** | [/how-to-build-your-own-jarvis](https://jarvis.driftworksstudios.com/how-to-build-your-own-jarvis) · archived in [`free/`](./free/) |
| Demo videos | **Yes** (watch) | YouTube @ManinaLabs |
| Landing-page UI inspiration | **Yes** (view source) | public HTML/CSS/JS |
| His GitHub JARVIS repo | **Does not exist** | no public kit repo found |

**There is no free full blueprint and no free source dump from him.** Everything past Chapter 1 of the book and all runnable kit code is paywalled.

---

## Free materials we captured

### 1. Blueprint Preview PDF (FREE)

- URL: https://jarvis.driftworksstudios.com/assets/jarvis-blueprint-preview.pdf  
- Local: `free/jarvis-blueprint-preview.pdf`  
- Text extract: `free/blueprint-preview-extracted.txt`  
- Contents: cover, license, letter, **full table of contents**, **Chapter 1 — System Architecture** (diagrams, six subsystems, turn flow, design principles), then “END OF FREE PREVIEW — buy full book”.

**Usable free intel from that PDF:**

- Architecture: Flask + Socket.IO ↔ orb UI over websocket  
- Brain: Anthropic Claude (cloud), two-model split  
- Voice: Coqui **XTTS** (speak/clone) + **Whisper** (listen)  
- Memory: **Chroma** + **SQLite** + markdown vault  
- Tools: ~50 functions + dispatcher  
- Monitors: background daemon loops  
- Builder: **Claude Code** (they assume you generate code with AI)  
- Hardware: Windows 11, NVIDIA **8GB+ VRAM**, Python 3.10/3.11, Git, Chrome  
- Module names hinted: `app.py`, `jarvis_state.py`, `jarvis_memory.py`, `jarvis_tools.py`, `jarvis_voice.py`, `xtts_server.py`, `jarvis_monitors.py`  
- TOC of what the **paid** book covers (so we know the roadmap, not the recipes)

### 2. How-to-build page (FREE)

- URL: https://jarvis.driftworksstudios.com/how-to-build-your-own-jarvis  
- Local: `free/how-to-build-your-own-jarvis.txt` (+ `.html`)  
- Contents: building blocks (brain, ears, voice, UI, memory, tools, glue) and the 7-step build order (text → TTS → STT → wake word → UI → memory → tools). No kit source.

### 3. YouTube demos (FREE to watch)

| Demo | Link |
|------|------|
| Voice Commands | https://www.youtube.com/watch?v=Ota84LrRqLA |
| Memory Recall | https://www.youtube.com/watch?v=2zyPY_LPVcg |
| Application Launching | https://www.youtube.com/watch?v=3rUS7Q7mNXQ |
| File Operations | https://www.youtube.com/watch?v=REWb9jZ2QQk |
| Workflow Automation | https://www.youtube.com/watch?v=MuiCM6wEqtQ |
| Neural Interface | https://www.youtube.com/watch?v=nVLhx0fh1xQ |
| Build vlog “Update 1” | https://www.youtube.com/watch?v=msZaS_AAmpg |

These show **behavior**, not downloadable code.

### 4. Public site front-end (FREE to study)

- `site.css`, `site.js`, Three.js particle orb hero — visual language only  
- Not the assistant runtime

### 5. GitHub check

- `github.com/sammanina` — 1 unrelated repo (`ELEOS-Website`), **no JARVIS**  
- `github.com/ManinaLabs` — 404  
- `github.com/driftworks` — 0 repos  

He is **not** open-sourcing the kit.

---

## What’s locked behind paywall (do not expect free)

- Chapters 2–13 + appendices (setup prompts, personality prompts, voice-clone recipe, tool schemas, orb build, security, checklist)  
- Starter Kit source + holographic UI project  
- Creator Kit trained voice + wake-word pack + 50+ skills  
- Founder coaching  

Terms forbid redistributing purchased materials. We rebuild from **public architecture + free OSS**, not by ripping paid kits.

---

## Free rebuild path (no ManinaLabs purchase)

Use his **free architecture** as the map; use **open-source / freemium APIs** as the bricks:

| His piece | Free / cheap substitute |
|-----------|-------------------------|
| Blueprint Ch.2+ prompts | We write our own prompts (Claude Code free tier / Cursor / local) |
| Claude brain | Anthropic free credits if any, else **Groq free tier**, **OpenRouter free models**, or **Ollama** local (fully free) |
| Claude Code builder | Cursor (this env), or free Claude/GPT tiers carefully |
| Whisper STT | `faster-whisper` (open source, free) |
| XTTS clone voice | Coqui TTS / XTTS (open source, free; needs GPU) — or free **Edge-TTS** (no clone) |
| Wake word | **openWakeWord** (free) |
| Chroma + SQLite | open source, free |
| Flask + Socket.IO | open source, free |
| Browser control | **Playwright** (free) |
| Orb UI | Three.js (free) — we already have orb experiments on repo branches |
| Desktop control | `pywinauto` / PowerShell (free) |
| Weather/news | free public APIs |

**True $0 path:** Ollama (local LLM) + faster-whisper + Edge-TTS + openWakeWord + SQLite + Playwright + simple Flask/FastAPI UI. No clone voice, weaker “butler” quality, but free.

**Low-cost path (still no kit):** same stack + Anthropic/Groq API when you can spare a few dollars — matches his disclosed design much closer.

---

## Already in this repo (also free to you)

Remote branches with working prototypes (not from ManinaLabs):

- `claude/jarvis-ai-assistant-4sfEQ` — fullest (FastAPI, Claude/Groq, tools, Playwright)  
- `claude/revert-vite-config-IfUHA` — Node + Claude tools + Edge TTS  
- `claude/jarvis-voice-assistant-5PuMM` — offline Ollama orb  
- `cursor/jarvis-phase1-foundation-6cb2` — Electron shell  

These are the best **free starting points** you already own, mapped against his free architecture in [REPO-GAP.md](./REPO-GAP.md).

---

## Bottom line

1. **Yes, he has a blueprint** — but only **Chapter 1 is free**; the rest costs $29+.  
2. **No free kit / no free GitHub source** from ManinaLabs.  
3. We archived every free artifact under `docs/jarvis-research/free/`.  
4. Rebuild = free public architecture + free OSS stack (+ optional cheap API keys later), using your existing JARVIS branches as code base.
