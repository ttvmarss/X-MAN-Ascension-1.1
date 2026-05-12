"""
J.A.R.V.I.S. - Iron Man Desktop AI
pip install edge-tts sounddevice SpeechRecognition numpy
Offline AI: install Ollama (ollama.com) → ollama pull tinyllama
"""

import tkinter as tk
import threading
import asyncio
import ctypes
import os
import json
import urllib.request
import urllib.error
import math
import tempfile

# ── Windows built-in MP3 player (no extra install) ───────────────────────────
_winmm = ctypes.windll.winmm

def _mci_play(path: str):
    safe = path.replace("/", "\\")
    _winmm.mciSendStringW(f'open "{safe}" type mpegvideo alias _j', None, 0, None)
    _winmm.mciSendStringW('play _j wait', None, 0, None)
    _winmm.mciSendStringW('close _j', None, 0, None)

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    import edge_tts
    EDGE_TTS = True
except ImportError:
    EDGE_TTS = False

try:
    import sounddevice as sd
    import numpy as np
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

# ── Theme ─────────────────────────────────────────────────────────────────────
BG    = "#000812"
PANEL = "#00060f"
CYAN  = "#00d4ff"
BLUE  = "#0055cc"
DIM   = "#001f33"
GOLD  = "#ff8c00"
GREEN = "#00ff88"
WHITE = "#cceeff"
GRAY  = "#223344"

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


# ── Ollama ────────────────────────────────────────────────────────────────────
def ask_ollama(history: list) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-20:]
    body = json.dumps({"model": OLLAMA_MODEL, "messages": messages,
                       "stream": False}).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=body,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["message"]["content"].strip()
    except urllib.error.URLError:
        return ("My AI core is offline, sir. "
                "Please ensure Ollama is running with tinyllama installed.")
    except Exception as e:
        return f"An error in my language module, sir: {e}"


# ── Always-on VAD microphone (sounddevice — no pyaudio needed) ───────────────
class _MicListener:
    RATE            = 16000
    CHUNK           = 1600       # 100 ms
    THRESHOLD       = 0.012      # RMS energy threshold
    SILENCE_CHUNKS  = 14         # ~1.4 s silence ends phrase
    MIN_CHUNKS      = 4          # ~400 ms minimum speech

    def __init__(self, on_text, on_state):
        self._on_text  = on_text
        self._on_state = on_state
        self._rec      = sr.Recognizer() if SR else None
        self._buf      = []
        self._in_speech = False
        self._silence   = 0
        self._muted     = False
        self._stream    = None

    def mute(self, val: bool):
        self._muted     = val
        self._buf       = []
        self._in_speech = False
        self._silence   = 0

    def _cb(self, indata, frames, t, status):
        if self._muted:
            return
        rms = float(np.sqrt(np.mean(indata ** 2)))
        loud = rms > self.THRESHOLD

        if loud:
            if not self._in_speech:
                self._in_speech = True
                self._on_state("listening")
            self._silence = 0
            self._buf.append(indata.copy())
        elif self._in_speech:
            self._buf.append(indata.copy())
            self._silence += 1
            if self._silence >= self.SILENCE_CHUNKS:
                captured = list(self._buf)
                self._buf       = []
                self._in_speech = False
                self._silence   = 0
                self._on_state("idle")
                if len(captured) >= self.MIN_CHUNKS:
                    threading.Thread(
                        target=self._process, args=(captured,), daemon=True
                    ).start()

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

    def start(self):
        if not SD or not SR:
            return False
        try:
            self._stream = sd.InputStream(
                samplerate=self.RATE, channels=1, dtype="float32",
                blocksize=self.CHUNK, callback=self._cb,
            )
            self._stream.start()
            return True
        except Exception as e:
            print(f"[JARVIS] Mic error: {e}")
            return False


# ── HUD Canvas ────────────────────────────────────────────────────────────────
class HUD(tk.Canvas):
    COLORS = {"idle": CYAN, "listening": GREEN, "thinking": GOLD, "speaking": CYAN}

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, highlightthickness=0, **kw)
        self.state = "idle"
        self._tick = 0
        self.after(100, self._loop)

    def set_state(self, s: str):
        self.state = s

    def _loop(self):
        self._draw()
        self._tick += 1
        self.after(33, self._loop)

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 2 or h < 2:
            return
        cx, cy = w // 2, h // 2
        t   = self._tick * 0.04
        col = self.COLORS.get(self.state, CYAN)

        # Hex grid background
        for gx in range(0, w + 60, 60):
            for gy in range(0, h + 52, 52):
                ox = 30 if (gy // 52) % 2 else 0
                self._hex(gx + ox - 30, gy - 26, 18)

        R = min(cx, cy) - 18

        # Outer ring + tick marks
        self.create_oval(cx-R, cy-R, cx+R, cy+R, outline=GRAY, width=1)
        for i in range(72):
            ang = math.radians(i * 5)
            ln  = 10 if i % 9 == 0 else (6 if i % 3 == 0 else 3)
            fc  = CYAN if i % 9 == 0 else (GRAY if i % 3 == 0 else DIM)
            self.create_line(
                cx + (R - ln) * math.cos(ang), cy + (R - ln) * math.sin(ang),
                cx + R * math.cos(ang),         cy + R * math.sin(ang),
                fill=fc, width=1)

        # Arc 1 — slow CW
        r1 = R - 14
        self.create_arc(cx-r1, cy-r1, cx+r1, cy+r1,
                        start=(t * 25) % 360, extent=250,
                        outline=CYAN, width=2, style="arc")

        # Arc 2 — CCW
        r2 = R - 30
        a2 = (-t * 38) % 360
        self.create_arc(cx-r2, cy-r2, cx+r2, cy+r2,
                        start=a2, extent=170, outline=BLUE, width=2, style="arc")
        self.create_arc(cx-r2, cy-r2, cx+r2, cy+r2,
                        start=a2 + 200, extent=70, outline=BLUE, width=1, style="arc")

        # Arc 3 — fast, state color
        r3 = R - 50
        a3 = (t * 65) % 360
        self.create_arc(cx-r3, cy-r3, cx+r3, cy+r3,
                        start=a3, extent=110, outline=col, width=3, style="arc")
        self.create_arc(cx-r3, cy-r3, cx+r3, cy+r3,
                        start=a3 + 160, extent=40, outline=col, width=1, style="arc")

        # Inner pulsing ring
        pulse = math.sin(t * (3 if self.state == "speaking" else 1.2)) * 0.5 + 0.5
        r4    = R - 72 + pulse * 6
        rc2   = col if self.state != "idle" else DIM
        self.create_oval(cx-r4, cy-r4, cx+r4, cy+r4,
                         outline=rc2, width=1 + int(pulse * 3))

        # Arc reactor centre
        rc = 22
        self.create_oval(cx-rc, cy-rc, cx+rc, cy+rc, outline=CYAN, width=2)
        for i in range(3):
            ang = math.radians(i * 120 - 90 + t * 15)
            self.create_line(
                cx + 6  * math.cos(ang), cy + 6  * math.sin(ang),
                cx + rc * math.cos(ang), cy + rc * math.sin(ang),
                fill=CYAN, width=2)
        self.create_oval(cx-5, cy-5, cx+5, cy+5, fill=col, outline="")

        # Labels
        self.create_text(cx, cy - R - 14, text="J.A.R.V.I.S.",
                         fill=CYAN, font=("Consolas", 13, "bold"), anchor="n")
        self.create_text(cx, cy + R + 5, text=self.state.upper(),
                         fill=col, font=("Consolas", 9), anchor="n")
        self.create_text(18,     cy, text="STARK\nSYSTEMS", fill=GRAY,
                         font=("Consolas", 7), anchor="w")
        self.create_text(w - 18, cy, text="AI\nCORE", fill=GRAY,
                         font=("Consolas", 7), anchor="e")

        # Waveform
        if self.state in ("speaking", "listening"):
            bars, bw, sp = 24, 5, 3
            bx0 = cx - bars * (bw + sp) // 2
            spd = 4 if self.state == "speaking" else 6
            for i in range(bars):
                bh = abs(math.sin(t * spd + i * 0.45)) * 22 + 4
                bx = bx0 + i * (bw + sp)
                self.create_rectangle(bx, h - 10 - bh, bx + bw, h - 10,
                                      fill=col, outline="")

    def _hex(self, x, y, r):
        pts = []
        for i in range(6):
            a = math.radians(60 * i - 30)
            pts += [x + r * math.cos(a), y + r * math.sin(a)]
        self.create_polygon(pts, outline=DIM, fill="", width=1)


# ── Main app ──────────────────────────────────────────────────────────────────
class Jarvis:
    def __init__(self, root: tk.Tk):
        self.root     = root
        self.root.title("J.A.R.V.I.S.")
        self.root.configure(bg=BG)
        self.root.geometry("960x740")
        self.root.minsize(700, 500)

        self._speaking      = False
        self._history: list = []
        self._engine        = None

        self._init_tts()
        self._build_ui()
        self._start_mic()
        self.root.after(600, self._greet)

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
        self._hud.set_state("speaking")
        try:
            if EDGE_TTS:
                asyncio.run(self._edge_speak(text))
            elif self._engine:
                self._engine.say(text)
                self._engine.runAndWait()
        except Exception as e:
            print(f"[JARVIS] TTS error: {e}")
        finally:
            self._speaking = False
            self._mic.mute(False)
            self._hud.set_state("idle")

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
        self._mic = _MicListener(
            on_text  = lambda t: self.root.after(0, lambda: self._on_input(t)),
            on_state = lambda s: self.root.after(0, lambda: self._hud.set_state(s)
                                                 if not self._speaking else None),
        )
        ok = self._mic.start()
        if ok:
            self._append_sys("Microphone active — just speak, sir.")
        else:
            self._append_sys(
                "Voice input unavailable. "
                "Run: pip install sounddevice SpeechRecognition numpy"
            )

    # ── Input processing ──────────────────────────────────────────────────────
    def _on_input(self, text: str):
        if self._speaking:
            return
        self._append("YOU", text, "you")
        self._hud.set_state("thinking")
        threading.Thread(target=self._respond, args=(text,), daemon=True).start()

    def _respond(self, text: str):
        self._history.append({"role": "user", "content": text})
        reply = ask_ollama(self._history)
        self._history.append({"role": "assistant", "content": reply})
        self.root.after(0, lambda r=reply: self._append("JARVIS", r, "jarvis"))
        self.speak(reply)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # HUD takes top portion
        self._hud = HUD(self.root, height=370)
        self._hud.pack(fill="x")

        tk.Frame(self.root, bg=CYAN, height=1).pack(fill="x")

        # Chat log — voice only, no text box
        chat_frame = tk.Frame(self.root, bg=PANEL)
        chat_frame.pack(fill="both", expand=True)

        self._chat = tk.Text(
            chat_frame, bg=PANEL, fg=WHITE,
            font=("Consolas", 11), relief="flat",
            padx=18, pady=12, wrap="word",
            state="disabled", borderwidth=0,
            selectbackground=BLUE, selectforeground=WHITE,
        )
        sb = tk.Scrollbar(chat_frame, command=self._chat.yview,
                          bg=BG, troughcolor=DIM, relief="flat")
        self._chat.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._chat.pack(fill="both", expand=True)

        self._chat.tag_config("you",    foreground="#ffcc44", font=("Consolas", 11, "bold"))
        self._chat.tag_config("jarvis", foreground=CYAN,      font=("Consolas", 11, "bold"))
        self._chat.tag_config("msg",    foreground=WHITE,     font=("Consolas", 11))
        self._chat.tag_config("sys",    foreground=GRAY,      font=("Consolas", 9, "italic"))

    def _append(self, speaker: str, msg: str, tag: str):
        self._chat.config(state="normal")
        if self._chat.index("end-1c") != "1.0":
            self._chat.insert("end", "\n")
        self._chat.insert("end", f"{speaker}: ", tag)
        self._chat.insert("end", msg + "\n", "msg")
        self._chat.see("end")
        self._chat.config(state="disabled")

    def _append_sys(self, msg: str):
        self._chat.config(state="normal")
        if self._chat.index("end-1c") != "1.0":
            self._chat.insert("end", "\n")
        self._chat.insert("end", f"[ {msg} ]\n", "sys")
        self._chat.see("end")
        self._chat.config(state="disabled")

    def _greet(self):
        msg = "Good day, sir. All systems are fully operational. How may I be of service?"
        self._append("JARVIS", msg, "jarvis")
        self.speak(msg)


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    Jarvis(root)
    root.mainloop()
