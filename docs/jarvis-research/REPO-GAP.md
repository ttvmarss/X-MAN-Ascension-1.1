# Repo Gap Analysis — X-MAN-Ascension-1.1

This repository’s `main` branch is **X-MAN Ascension** (Fortnite / Windows tweak panel), not JARVIS.

Parallel JARVIS experiments already exist on remotes:

| Branch | Stack | Closest ManinaLabs tier |
|--------|-------|-------------------------|
| `claude/jarvis-ai-assistant-4sfEQ` | Python FastAPI, Claude/Groq, Fish TTS, Playwright, SQLite, Cloudflare tunnel, PC agent | Creator-ish (different TTS/backend) |
| `claude/revert-vite-config-IfUHA` | Node Express, Claude tools, Edge TTS, better-sqlite3, LAN iPhone | Starter → Creator hybrid |
| `claude/jarvis-voice-assistant-5PuMM` | Tkinter + Ollama + Edge TTS + Google STT | Early Starter / demo |
| `cursor/jarvis-phase1-foundation-6cb2` | Electron + Web Speech + keyword router, no LLM | Pre-Starter shell |

## ManinaLabs vs our existing code

| Piece | ManinaLabs (public) | Existing JARVIS branches |
|-------|---------------------|--------------------------|
| Backend | Flask + Socket.IO | FastAPI / Express / Electron |
| Brain | Claude API (two-model) | Claude / Groq / Ollama |
| TTS | Coqui XTTS (clone) | Fish Audio / Edge-TTS / Web Speech |
| STT | Whisper local | Web Speech / Google / optional Whisper |
| Memory | Chroma + SQLite + markdown | SQLite / JSON |
| UI | Orb HUD web UI | Three.js orb (aligned visually) |
| Tools | ~50 Windows skills | Smaller tool sets + Playwright |
| Build tooling | Claude Code prompt book | Ad-hoc agent builds |

## Recommendation

1. Treat ManinaLabs docs in this folder as the **north-star architecture**.
2. Prefer converging on **one** runtime (recommend Python: either adopt Flask+Socket.IO to match Blueprint, or keep FastAPI+WS from `jarvis-ai-assistant` and map modules 1:1).
3. Prioritize tooling installs from [TOOLING.md](./TOOLING.md): Whisper, XTTS (or Edge fallback), Chroma, Anthropic SDK, browser automation, wake word.
4. Do **not** vendor ManinaLabs paid kit files into this repo.
