# JARVIS

> Just A Rather Very Intelligent System.

Voice-first AI assistant for Windows 10 and iPhone. Talks back in a British
accent. Free voice. No Python required.

---

## 🚀 Easiest possible setup

**1.** Install **Node.js LTS** from <https://nodejs.org/> (just click the green
LTS button, run installer, accept defaults).

**2.** Get an **Anthropic API key** from <https://console.anthropic.com/>
(sign up → API Keys → Create Key → copy it).

**3.** Double-click **`INSTALL.bat`** in this folder.
- It asks for your API key (paste it)
- It asks what JARVIS should call you
- It installs everything automatically (5-10 min)
- At the end it offers to launch JARVIS for you

**4.** Open `https://localhost:8000` in Chrome → accept the security warning
→ click → allow mic → start talking.

**That's it.** For phone use, scan the QR code in the JARVIS console with
your iPhone.

---

## Step-by-step with every click

See **[STEP-BY-STEP.md](./STEP-BY-STEP.md)** for the bulletproof walkthrough
including every screen, every click, and every error you might hit.

## Something not working?

Double-click **`doctor.bat`** — it checks 8 common things and tells you
exactly what's wrong.

## Full technical docs

See **[CLAUDE.md](./CLAUDE.md)** for the architecture, file layout, and tools.

---

## What can it do?

- "What time is it?"
- "Open Notepad"
- "Search for the weather in Tokyo"
- "Remember that I prefer React over Vue"
- "Add a task to call the dentist tomorrow"
- "Build me a Snake game in JavaScript"
- "Save a note: ideas for my novel"

It uses Claude AI with structured tool calls — it actually does the things,
not just describes them.

## Stack

- **Backend**: Node.js 18+ (Express + ws)
- **Frontend**: Vite + TypeScript + Three.js (audio-reactive particle orb)
- **AI**: Anthropic Claude (Haiku) with tool use
- **Voice in**: Web Speech API (PC Chrome) / MediaRecorder push-to-talk (iPhone)
- **Voice out**: Microsoft Edge neural TTS — **free, no API key, sounds amazing**
- **Memory**: SQLite + FTS5

## License

Personal use. Be excellent.
