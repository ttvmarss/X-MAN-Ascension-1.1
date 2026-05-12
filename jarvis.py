"""
J.A.R.V.I.S. — particle orb UI matching ethanplusai/jarvis web version
pip install edge-tts sounddevice SpeechRecognition numpy
Offline AI: install Ollama (ollama.com) → ollama pull tinyllama
"""

import tkinter as tk
import threading
import asyncio
import ctypes
import os, json, math, tempfile, time

try:
    import numpy as np
    NP = True
except ImportError:
    NP = False

try:
    import edge_tts
    EDGE_TTS = True
except ImportError:
    EDGE_TTS = False

try:
    import sounddevice as sd
    SD = True
except ImportError:
    SD = False

try:
    import speech_recognition as sr
    SR = True
except ImportError:
    SR = False

try:
    import pyttsx3
    PYTTSX = True
except ImportError:
    PYTTSX = False

# ── Windows built-in MP3 playback ─────────────────────────────────────────────
_winmm = ctypes.windll.winmm
def _mci_play(path: str):
    safe = path.replace("/", "\\")
    _winmm.mciSendStringW(f'open "{safe}" type mpegvideo alias _j', None, 0, None)
    _winmm.mciSendStringW('play _j wait', None, 0, None)
    _winmm.mciSendStringW('close _j', None, 0, None)

# ── Theme (matches ethanplusai/jarvis web UI) ─────────────────────────────────
BG       = "#050508"
CYAN     = "#0ea5e9"
PARTICLE = (76, 168, 232)     # idle/speaking particle color
P_LISTEN = (34, 197, 94)      # green while listening
P_THINK  = (110, 196, 255)    # brighter blue while thinking
DOT_ON   = "#22c55e"
DOT_WARN = "#eab308"
DOT_BLUE = "#0ea5e9"
TEXT_DIM  = "rgba(255,255,255,0.4)"
FONT      = ("Segoe UI", 11)
FONT_SM   = ("Segoe UI", 9)

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "tinyllama"
VOICE        = "en-GB-RyanNeural"
SYSTEM_PROMPT = (
    "You are J.A.R.V.I.S., Tony Stark's AI from Iron Man. "
    "Speak with intelligence, formality, and dry wit. "
    "Always address the user as 'sir'. "
    "Be concise — 1 to 3 sentences unless more detail is truly needed."
)

import urllib.request, urllib.error
def ask_ollama(history: list) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-20:]
    body = json.dumps({"model": OLLAMA_MODEL, "messages": messages,
                       "stream": False}).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["message"]["content"].strip()
    except urllib.error.URLError:
        return ("My AI core is offline, sir. "
                "Please ensure Ollama is running with tinyllama installed.")
    except Exception as e:
        return f"An error in my language module, sir: {e}"


# ── Always-on mic (sounddevice VAD, no pyaudio) ───────────────────────────────
class _Mic:
    RATE   = 16000
    CHUNK  = 1600
    THRESH = 0.013
    SIL    = 14
    MIN    = 4

    def __init__(self, on_text, on_state):
        self._on_text  = on_text
        self._on_state = on_state
        self._rec      = sr.Recognizer() if SR else None
        self._buf      = []
        self._active   = False
        self._sil      = 0
        self._muted    = False

    def mute(self, v: bool):
        self._muted  = v
        self._buf    = []
        self._active = False
        self._sil    = 0

    def _cb(self, indata, frames, t, status):
        if self._muted:
            return
        rms  = float(np.sqrt(np.mean(indata ** 2)))
        loud = rms > self.THRESH
        if loud:
            if not self._active:
                self._active = True
                self._on_state("listening")
            self._sil = 0
            self._buf.append(indata.copy())
        elif self._active:
            self._buf.append(indata.copy())
            self._sil += 1
            if self._sil >= self.SIL:
                captured    = list(self._buf)
                self._buf   = []
                self._active = False
                self._sil   = 0
                self._on_state("idle")
                if len(captured) >= self.MIN:
                    threading.Thread(target=self._process,
                                     args=(captured,), daemon=True).start()

    def _process(self, chunks):
        if not self._rec:
            return
        audio_np  = np.concatenate(chunks, axis=0).flatten()
        pcm       = (audio_np * 32767).astype(np.int16).tobytes()
        audio_obj = sr.AudioData(pcm, self.RATE, 2)
        try:
            text = self._rec.recognize_google(audio_obj).strip()
            if text:
                self._on_text(text)
        except Exception:
            pass

    def start(self) -> bool:
        if not SD or not SR or not NP:
            return False
        try:
            self._stream = sd.InputStream(
                samplerate=self.RATE, channels=1, dtype="float32",
                blocksize=self.CHUNK, callback=self._cb)
            self._stream.start()
            return True
        except Exception as e:
            print(f"[JARVIS] Mic error: {e}")
            return False


# ── Particle orb canvas ───────────────────────────────────────────────────────
class OrbCanvas(tk.Canvas):
    N = 380

    # Normalised sphere radius per state (0–1 maps to 0–half window)
    _TARGET_R = {"idle": 0.52, "listening": 0.40, "thinking": 0.30, "speaking": 0.44}
    # RGB particle colors per state
    _COLORS   = {
        "idle":      (76,  168, 232),
        "listening": (34,  197, 94),
        "thinking":  (110, 196, 255),
        "speaking":  (90,  184, 240),
    }
    # Status dot colors
    _DOT_COL  = {"idle": DOT_ON, "listening": DOT_ON,
                 "thinking": DOT_WARN, "speaking": DOT_BLUE}

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, highlightthickness=0, **kw)
        self.state      = "idle"
        self._tick      = 0
        self._t         = 0.0
        self._cur_r     = self._TARGET_R["idle"]
        self._chat_lines: list[tuple[str, str]] = []  # (speaker, text)

        rng           = np.random.default_rng(42)
        theta         = rng.uniform(0, 2 * np.pi, self.N)
        phi           = np.arccos(rng.uniform(-1, 1, self.N))
        r             = rng.uniform(0.2, 1.0, self.N) ** (1 / 3)
        self._px      = r * np.sin(phi) * np.cos(theta)
        self._py      = r * np.sin(phi) * np.sin(theta)
        self._pz      = r * np.cos(phi)
        self._vx      = rng.uniform(-0.0025, 0.0025, self.N)
        self._vy      = rng.uniform(-0.0025, 0.0025, self.N)
        self._vz      = rng.uniform(-0.0025, 0.0025, self.N)
        self._ry      = 0.0
        self._rx      = 0.0

        self.after(200, self._loop)

    def set_state(self, s: str):
        self.state = s

    def add_line(self, speaker: str, text: str):
        self._chat_lines.append((speaker, text))
        if len(self._chat_lines) > 6:
            self._chat_lines.pop(0)

    # ── animation loop ────────────────────────────────────────────────────────
    def _loop(self):
        w = self.winfo_width()
        h = self.winfo_height()
        if w > 10 and h > 10:
            self._step()
            self._render(w, h)
        self._tick += 1
        self._t    += 0.033
        self.after(33, self._loop)

    def _step(self):
        self._cur_r += (self._TARGET_R.get(self.state, 0.52) - self._cur_r) * 0.04

        self._px += self._vx
        self._py += self._vy
        self._pz += self._vz

        dist = np.sqrt(self._px**2 + self._py**2 + self._pz**2)
        mask = dist > 1.0
        if np.any(mask):
            self._px[mask] /= dist[mask]
            self._py[mask] /= dist[mask]
            self._pz[mask] /= dist[mask]
            self._vx[mask] *= -0.5
            self._vy[mask] *= -0.5
            self._vz[mask] *= -0.5

        # Pull toward centre (tighter states pull more)
        pull = 0.002 * max(0, (0.52 - self._cur_r) / 0.22)
        self._px *= (1 - pull)
        self._py *= (1 - pull)
        self._pz *= (1 - pull)

        spd = 0.005 if self.state == "thinking" else 0.0018
        self._ry += spd
        self._rx += spd * 0.28

    def _project(self, w, h):
        scale = min(w, h) * self._cur_r
        cy_r  = math.cos(self._ry);  sy_r = math.sin(self._ry)
        cx_r  = math.cos(self._rx);  sx_r = math.sin(self._rx)

        rx  = self._px * cy_r - self._pz * sy_r
        rz  = self._px * sy_r + self._pz * cy_r
        ry  = self._py
        ry2 = ry * cx_r - rz * sx_r
        rz2 = ry * sx_r + rz * cx_r

        fov  = 2.8
        persp = fov / (fov + rz2 * 0.25)
        sx   = w / 2 + rx  * scale * persp
        sy   = h / 2 + ry2 * scale * persp
        return sx, sy, rz2

    def _blend(self, rgb: tuple, alpha: float) -> str:
        bg = (5, 5, 8)
        r = int(bg[0] + (rgb[0] - bg[0]) * min(1.0, max(0.0, alpha)))
        g = int(bg[1] + (rgb[1] - bg[1]) * min(1.0, max(0.0, alpha)))
        b = int(bg[2] + (rgb[2] - bg[2]) * min(1.0, max(0.0, alpha)))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _render(self, w, h):
        self.delete("all")
        sx, sy, sz = self._project(w, h)
        order = np.argsort(sz)
        col   = self._COLORS.get(self.state, (76, 168, 232))

        # Connection lines (thinking state only, capped at 55 lines)
        if self.state == "thinking":
            drawn = 0
            step  = max(1, self.N // 80)
            for i in range(0, self.N, step):
                if drawn >= 55:
                    break
                for j in range(i + 1, min(i + 6, self.N)):
                    d2 = (sx[i]-sx[j])**2 + (sy[i]-sy[j])**2
                    if d2 < 2800:
                        a  = (1 - d2 / 2800) * 0.25
                        lc = self._blend(col, a)
                        self.create_line(sx[i], sy[i], sx[j], sy[j],
                                         fill=lc, width=1)
                        drawn += 1

        # Particles back → front
        for idx in order:
            x, y, z = float(sx[idx]), float(sy[idx]), float(sz[idx])
            depth   = (z + 1) / 2.0
            size    = 1.2 + depth * 1.8
            alpha   = 0.25 + depth * 0.55

            if self.state in ("speaking", "listening"):
                osc   = math.sin(self._t * 5 + idx * 0.12) * 0.5 + 0.5
                size *= 1 + osc * 0.35

            c = self._blend(col, alpha)
            self.create_oval(x-size, y-size, x+size, y+size, fill=c, outline="")

        # ── Overlay UI ────────────────────────────────────────────────────────
        dc = self._DOT_COL.get(self.state, DOT_ON)

        # Bottom centre: status dot + label
        dot_x, dot_y = w // 2 - 55, h - 32
        self.create_oval(dot_x, dot_y, dot_x + 8, dot_y + 8, fill=dc, outline="")
        self.create_text(dot_x + 14, dot_y + 4,
                         text=self.state.upper(), fill=dc,
                         font=("Segoe UI", 9, "bold"), anchor="w")

        # Bottom right: "J.A.R.V.I.S."
        self.create_text(w - 20, h - 28, text="J.A.R.V.I.S.",
                         fill="#ffffff44", font=("Segoe UI", 9), anchor="e")

        # Transcript overlay (last few lines, bottom of orb)
        if self._chat_lines:
            y_base = h - 60
            for speaker, text in reversed(self._chat_lines[-4:]):
                display = f"{speaker}: {text}"
                if len(display) > 72:
                    display = display[:69] + "…"
                fc = "#ffffffcc" if speaker == "JARVIS" else "#ffcc44cc"
                self.create_text(w // 2, y_base, text=display,
                                 fill=fc, font=("Segoe UI", 10),
                                 anchor="s", width=w - 60)
                y_base -= 22


# ── Main application ──────────────────────────────────────────────────────────
class Jarvis:
    def __init__(self, root: tk.Tk):
        self.root     = root
        self.root.title("J.A.R.V.I.S.")
        self.root.configure(bg=BG)
        self.root.geometry("900x660")
        self.root.minsize(600, 480)

        self._speaking      = False
        self._history: list = []
        self._engine        = None

        self._init_tts()
        self._build_ui()
        self._start_mic()
        self.root.after(700, self._greet)

    # ── TTS ───────────────────────────────────────────────────────────────────
    def _init_tts(self):
        if PYTTSX:
            try:
                self._engine = pyttsx3.init()
                for v in self._engine.getProperty('voices'):
                    if any(x in v.name.lower() for x in ('david', 'george', 'mark')):
                        self._engine.setProperty('voice', v.id)
                        break
                self._engine.setProperty('rate', 148)
            except Exception:
                self._engine = None

    def _speak_worker(self, text: str):
        self._speaking = True
        self._mic.mute(True)
        self._orb.set_state("speaking")
        try:
            if EDGE_TTS:
                asyncio.run(self._edge_speak(text))
            elif self._engine:
                self._engine.say(text)
                self._engine.runAndWait()
        except Exception as e:
            print(f"[JARVIS] TTS: {e}")
        finally:
            self._speaking = False
            self._mic.mute(False)
            self._orb.set_state("idle")

    async def _edge_speak(self, text: str):
        comm = edge_tts.Communicate(text, VOICE, rate="-8%", pitch="-10Hz")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            path = f.name
        await comm.save(path)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _mci_play, path)
        try:
            os.unlink(path)
        except Exception:
            pass

    def speak(self, text: str):
        threading.Thread(target=self._speak_worker, args=(text,), daemon=True).start()

    # ── Mic ───────────────────────────────────────────────────────────────────
    def _start_mic(self):
        self._mic = _Mic(
            on_text  = lambda t: self.root.after(0, lambda: self._on_input(t)),
            on_state = lambda s: self.root.after(
                0, lambda: self._orb.set_state(s) if not self._speaking else None),
        )
        if not self._mic.start():
            print("[JARVIS] pip install sounddevice SpeechRecognition numpy")

    # ── Input ─────────────────────────────────────────────────────────────────
    def _on_input(self, text: str):
        if self._speaking:
            return
        self._orb.add_line("YOU", text)
        self._orb.set_state("thinking")
        threading.Thread(target=self._respond, args=(text,), daemon=True).start()

    def _respond(self, text: str):
        self._history.append({"role": "user", "content": text})
        reply = ask_ollama(self._history)
        self._history.append({"role": "assistant", "content": reply})
        self.root.after(0, lambda r=reply: self._orb.add_line("JARVIS", r))
        self.speak(reply)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Orb fills the entire window — transcript overlaid on canvas
        self._orb = OrbCanvas(self.root)
        self._orb.pack(fill="both", expand=True)

    def _greet(self):
        msg = "Good day, sir. All systems are fully operational. How may I be of service?"
        self._orb.add_line("JARVIS", msg)
        self.speak(msg)


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    Jarvis(root)
    root.mainloop()
