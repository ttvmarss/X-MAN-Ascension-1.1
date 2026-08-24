# Build Roadmap — Match Public Methodology

Phased plan aligned with ManinaLabs’ free guide + Blueprint chapter order. Use this to build **our** assistant; do not paste proprietary kit prompts.

## Phase 0 — Environment

- [ ] Windows 11 machine (or decide Linux/macOS fork consciously)
- [ ] Python 3.10/3.11, Git, Chrome
- [ ] NVIDIA CUDA if targeting XTTS clone voice
- [ ] Anthropic API key + Claude Code
- [ ] Local project directory (no cloud sync)

## Phase 1 — Skeleton + text brain

- [ ] Flask (or FastAPI) app process
- [ ] Config for strong vs cheap Claude models
- [ ] Personality system prompt (our own writing)
- [ ] CLI or simple HTTP chat loop: text in → text out

## Phase 2 — Realtime glue

- [ ] Socket.IO / WebSocket to browser UI
- [ ] Shared state module as import leaf
- [ ] Turn handler with timeouts on every network call

## Phase 3 — Voice out

- [ ] XTTS server subprocess (or Edge-TTS / Piper fallback)
- [ ] Sentence streaming from LLM → TTS → speakers
- [ ] Fail-soft to Windows / system voice

## Phase 4 — Voice in + wake word

- [ ] Mic capture + VAD / end-of-utterance
- [ ] Whisper (faster-whisper) transcription
- [ ] Wake word “JARVIS” (openWakeWord / Porcupine / etc.)

## Phase 5 — Memory

- [ ] SQLite conversation log
- [ ] Chroma (or equivalent) semantic recall
- [ ] Markdown vault for durable notes
- [ ] Retrieve-and-prepend on each turn

## Phase 6 — Tools (~50 skills, grow gradually)

Start with 5–10, then expand:

1. Time / date  
2. Weather  
3. Web search  
4. Open application  
5. File search  
6. Browser navigate (Playwright)  
7. Reminder  
8. System status (CPU/GPU/RAM)  
9. Clipboard note  
10. Spotify / media (optional)  

Then: Outlook/calendar, Word/Excel, WolframAlpha, news, security monitor hooks.

## Phase 7 — Orb UI

- [ ] Particle / holographic orb reacting to audio amplitude
- [ ] Telemetry panels (CPU, GPU, network, weather)
- [ ] Chat transcript
- [ ] Modes: standby / awake / workspace

## Phase 8 — Monitors

- [ ] Background daemons with isolated failure
- [ ] Shared “speak” channel so monitors don’t barge over replies
- [ ] Security / health / file / clipboard watchers as needed

## Phase 9 — Hardening

- [ ] Security chapter practices: confirm destructive actions, sandbox tools, secret hygiene
- [ ] Startup orchestration script
- [ ] Troubleshooting checklist per milestone

## Success criteria (from public copy)

| Milestone | Bar |
|-----------|-----|
| Weekend | Talking assistant (STT ↔ LLM ↔ TTS) |
| 1–2 weeks evenings | Cloned voice + reactive UI + memory + working tool set |
| Creator-parity | Wake word, 50+ skills, PC control, monitors |
