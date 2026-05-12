# JARVIS

> Just A Rather Very Intelligent System.

A voice-first AI assistant for Windows 10 and iPhone. Pure Node.js + browser —
no Python, no paid TTS, no cloud lock-in beyond a Claude API key.

Talk to it. It talks back with a British-accented neural voice (free, via
Microsoft Edge). It opens apps, browses the web, remembers things, manages
tasks, and can spawn Claude Code to build whole projects.

## Quick start

```bash
# On Windows 10:
setup_windows.bat       # one-time setup
# (edit .env, paste your Anthropic API key)
start_jarvis.bat        # run it
```

Open the URL it prints. Click → allow mic → speak.

For your iPhone: scan the QR code in the console with your phone camera, on
the same WiFi.

See [CLAUDE.md](./CLAUDE.md) for full docs.

## Stack

- **Backend**: Node.js 18+ (Express + ws)
- **Frontend**: Vite + TypeScript + Three.js (audio-reactive particle orb)
- **AI**: Anthropic Claude (Haiku for speed) with tool use
- **Voice in**: Web Speech API (PC) / MediaRecorder + Whisper (iPhone)
- **Voice out**: Microsoft Edge neural TTS — free, no API key
- **Memory**: SQLite + FTS5

## License

Personal use. Be excellent.
