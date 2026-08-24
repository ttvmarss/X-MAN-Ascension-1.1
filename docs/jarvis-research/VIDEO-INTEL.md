# TikTok Video Intelligence — @maninalabs

Downloaded and analyzed **7 TikToks** (YouTube blocked bot checks in this environment).  
Clips: `/opt/cursor/artifacts/jarvis-tiktok-clips/` · Frames/transcripts under `/tmp/jarvis-videos/`.

## Videos watched / clipped

| ID | Topic | Plays | Local clip |
|----|-------|------:|------------|
| 7641701254854413598 | Self-diagnostics | 255K | ✅ |
| 7645469556084886797 | CAD / prototypes / VRAM | 102K | ✅ |
| 7648406134486748446 | Project direction → power/fusion first | 43K | ✅ |
| 7653280477410823455 | Intruder caught in 4s | 391K | ✅ |
| 7665488835219934494 | Glasses all-day vision | 47K | ✅ |
| 7669527602415144222 | Self-rewrite + fingerprint gate | 65K | ✅ |
| 7672910693833739550 | Glasses identify rock | 13K | ✅ |

---

## Hard tech evidence (from video, not marketing copy)

### Confirmed stack (on-screen logs / UI)

From **diagnostics** video terminal + HUD:

| Evidence | Value |
|----------|-------|
| Frontend URL | `http://localhost:3000` (orb UI in browser) |
| Also seen | `localhost:5000` (self-mod video — Flask default) |
| Runtime | **Python 3.10.12** |
| Machine (that clip) | MacBook Pro · x86 · 10 cores · **32 GB RAM** |
| APIs validated in log | **OpenAI** · **ElevenLabs** · **Spotify** |
| Apps detected | Chrome, Spotify |
| Browser control clue | Failure: **“Chrome debug port”** → Chrome DevTools / Playwright / CDP |
| OS (other clips) | **Windows 11** taskbar also appears (multi-machine) |
| Dev tools visible | VS Code, Discord, Photoshop/Premiere (creator machine) |

### Python module names visible on screen (self-rewrite HUD)

```
jarvis_main.py
jarvis_core.py
jarvis_vision.py
jarvis_voice.py
jarvis_state.py
jarvis_personality.py
jarvis_content.py
jarvis_context.py
jarvis_memory.py
jarvis_goals.py
machine_good.py
```

UI chrome text: **“JARVIS - NEURAL OPERATING SYSTEM”** · STATUS ONLINE · COMMAND CENTER · NEURAL LINK ACTIVE.

This matches the free Blueprint’s modular layout (`jarvis_state.py` as shared state, etc.).

### Voice / UX behavior

- British butler TTS (video analysis: **ElevenLabs** in logs; Blueprint kit path uses **XTTS** — personal system may use both)
- Voice command → action without mouse (“Run a full system check…”)
- Subtitles under orb stream as he speaks (“Fully operational and standing by, sir.”)
- Orb: cyan particle sphere; alert state turns **red** on intrusion

---

## Capability demos → rebuild features

### 1. Self-diagnostics
**Command:** “Run a full system check…”  
**Behavior:** Speaks ack → rapidly opens browser (Wikipedia AI, Google) + Spotify as live control tests → reports `54 passed`, critical: Chrome debug port, CPU temp missing.  
**Build:** `psutil` + platform info + API key ping + process list + Playwright/CDP smoke tests + WebSocket log stream to UI.

### 2. Hardware-aware CAD refusal
**Command:** Give 3D modeling / CAD ability.  
**JARVIS:** Already rationing **VRAM** between browser automation, vision, language — adding 3D engine would break things; needs new hardware.  
**Build:** Inject live GPU/VRAM into system prompt; capability flags; honest refusals.

### 3. Self-code edit with biometric gate
**Flow:** AI drafts diff → user reviews → “I approve” → phone **JarvisCompanion** “Approve Self-Edit” + **fingerprint** → tests `151 passed / 0 failed` → **restarts itself**.  
**Build:** Diff preview · mobile companion · biometric step-up · test suite · controlled restart. Do **not** allow silent self-write.

### 4. Desk intruder guard (4 seconds)
Unrecognized face → red “INTRUDER DETECTED” → locks desk → pushes phone alert + snapshot → “stand down” requires fingerprint.  
**Build:** Webcam face ID loop · input lock · WebSocket/push to companion · biometric disarm.

### 5. Smart glasses vision
Meta Ray-Ban–style glasses → “what am I looking at?” → multimodal describe (rock/mineral). All-day “watching everything” companion mode.  
**Build:** Image capture from glasses/phone → VLM (GPT-4o / Claude vision) → TTS. Optional frame loop every few seconds.

### 6. Project steering / research agent
User: what would real Tony build first?  
JARVIS: suit is late; **power independence / compact fusion** first → offers to start project and pull research.  
**Build:** Goals file (`jarvis_goals.py`) · research tool · project scaffolding.

---

## Dialogue highlights (Whisper + video review)

**Diagnostics:** “Right, running a full system check now…” → “54 passed. Critical failures: Chrome debug port…”

**Prototypes:** “…rationing VRAM between browser automation, vision, and language reasoning… need new hardware. Full stop.”

**Direction:** “The suit is actually fairly late… advanced power source first… Shall I start a project… compact fusion…”

**Self-edit:** Fingerprint gate → “Verified. Applying the change… 151 passed. 0 failed. Restarting myself…”

**Intruder:** “Unrecognized person at your desk… standing guard… saved a snapshot.” / “Standing down, sir.”

**Glasses:** Accurate visual description of desk rock (metallic luster, possible iron oxide/meteoritic).

---

## Stack reconciliation (Blueprint vs TikTok personal build)

| Piece | Free Blueprint / kits | Seen in TikTok personal system |
|-------|----------------------|--------------------------------|
| Brain | Anthropic Claude | **OpenAI** key validated in logs (may also use Claude elsewhere) |
| TTS | Coqui XTTS (+ Creator voice) | **ElevenLabs** key validated |
| Frontend | Flask templates / orb | Browser UI `localhost:3000` **and** `localhost:5000` |
| Backend | Flask + Socket.IO | Python 3.10 · modular `jarvis_*.py` |
| Extras | Kit excludes CAD/vision cloud | Personal: vision, glasses, CAD ambition, companion app, self-mod |

**Implication for our free rebuild:** Prefer Blueprint architecture (Flask/FastAPI + Whisper + XTTS/Edge-TTS + Chroma) but mirror **module names and behaviors** proven in TikTok. Use OpenAI/ElevenLabs only if/when budget allows; Groq/Ollama/Edge-TTS work for $0.

---

## Companion app (JarvisCompanion)

Visible in intruder + self-edit videos:

- Dark UI with orb  
- Modes: CHAT · SPEAKING · HANDS-FREE  
- Biometric sheets: “Approve Self-Edit”, “JARVIS — Stand Down”  
- Talks to desktop over realtime channel  

Out of scope for Starter-parity; Phase-later for Creator+.

---

## What we could not get

- YouTube downloads blocked (bot sign-in) in this cloud VM  
- Some TikToks failed yt-dlp  
- No free source repo — only on-screen filenames  

---

## Rebuild priority from video evidence

1. Modular Python package matching `jarvis_*.py` names  
2. Orb UI on local web port + live captions  
3. Voice in/out + tool router  
4. Diagnostics skill (system + APIs + browser smoke test)  
5. Memory / goals / state files  
6. Security monitor (face guard) — optional  
7. Companion + biometrics — later  
8. Glasses / CAD — later (VRAM-aware flags first)
