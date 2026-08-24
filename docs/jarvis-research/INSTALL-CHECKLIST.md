# Install Checklist — Assistant Runtime Dependencies

Machine targets: Windows 11 + NVIDIA (Creator path). Adjust for Starter (CPU + browser voice).

## System packages

```text
Python 3.10 or 3.11
Git
Google Chrome
NVIDIA Game Ready / Studio driver + CUDA toolkit (for GPU voice)
Claude Code CLI
```

## Environment variables (example)

```bash
ANTHROPIC_API_KEY=sk-ant-...
# optional
OPENAI_API_KEY=
OPENROUTER_API_KEY=
WOLFRAM_APP_ID=
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
WEATHER_API_KEY=
```

## Python packages (ManinaLabs-aligned core)

Pin versions when scaffolding the real app; this is the **acquisition list**:

```text
anthropic
flask
flask-socketio
eventlet
# or: fastapi uvicorn websockets   # if keeping existing FastAPI branch

chromadb
openai-whisper
# preferred faster path:
faster-whisper

# TTS — Coqui XTTS stack is heavy; install per Coqui TTS docs for your CUDA version
TTS
torch
torchaudio

playwright
httpx
pydantic
python-dotenv
pyyaml
sounddevice
numpy
psutil

# Windows desktop automation (Creator-class skills)
pywinauto
pywin32
```

After Playwright:

```bash
playwright install chromium
```

## Wake-word options (pick one)

```text
openwakeword
# or Picovoice porcupine (needs access key)
# or sherpa-onnx
```

## Verify before coding

1. `python --version` → 3.10.x / 3.11.x  
2. `nvidia-smi` → ≥ 8 GB free VRAM ideal  
3. Claude Code can run a hello-world edit  
4. `ANTHROPIC_API_KEY` returns a short completion  
5. Mic records; speakers play a test WAV  
6. Project path is on a local disk (not OneDrive)
