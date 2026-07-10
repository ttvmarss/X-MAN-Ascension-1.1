# Download Jarvis (Phase 1)

## What to download

You only need **one file** to run Jarvis on Windows:

| File | Size | What it is |
|------|------|------------|
| `Jarvis-0.1.0-portable.exe` | ~72 MB | Double-click to run — no install required |

After downloading, move it to your Desktop (or anywhere you like) and double-click it.

## First run

1. Windows may show SmartScreen (“Windows protected your PC”). Click **More info**, then **Run anyway** — this is normal for unsigned apps.
2. Allow **microphone** access when prompted.
3. Jarvis will greet you aloud and start listening.
4. Say **“Hey Jarvis”** before your command, for example:
   - “Hey Jarvis, what time is it?”
   - “Hey Jarvis, my name is [your name]”
   - “Hey Jarvis, what is my name?”
   - “Hey Jarvis, what is the date?”

## Mic button

Bottom-right corner: tap to **mute** or **unmute** the microphone.

## Where memory is saved

Jarvis remembers your name and conversation on your PC at:

```
%APPDATA%\jarvis\jarvis-memory.json
```

Your name is stored encrypted in that file.

## Rebuild from source (optional)

If you prefer to build it yourself:

```bash
cd jarvis
npm install
npm run dist
```

The `.exe` will appear in `jarvis/dist/Jarvis-0.1.0-portable.exe`.

## Phase 1 limits

- Wake phrase required: start commands with “Hey Jarvis”
- Keyword-based replies only (time, date, name, greeting, help, clear memory)
- No phone app, smart-home, or code generation yet (later phases)
