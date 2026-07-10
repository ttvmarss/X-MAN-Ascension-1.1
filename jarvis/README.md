# Jarvis

Personal voice assistant desktop app — Phase 1 foundation.

## Requirements

- Node.js 18+
- npm

## Development

```bash
cd jarvis
npm install
npm start
```

## Build Windows executable

```bash
npm run dist
```

Output: `dist/Jarvis-0.1.0-portable.exe`

## Phase 1 capabilities

- Animated orb UI (idle, listening, processing, speaking)
- Continuous voice input with wake phrase ("Hey Jarvis")
- Voice output via system speech synthesis
- Mic mute/unmute
- Persistent memory (name + history) saved to disk with encrypted name field
- Commands: time, date, greeting, remember/recall name, clear memory, help

## Memory file location

- Windows: `%APPDATA%/jarvis/jarvis-memory.json`
- Linux (dev): `~/.config/jarvis/jarvis-memory.json`

## Project structure

```
jarvis/
  main/       — Electron main process, IPC, memory store
  renderer/   — Orb canvas, voice UI, app logic
  shared/     — Greetings and command modules (Node tests)
```
