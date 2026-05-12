"""
J.A.R.V.I.S. - Iron Man Desktop AI
Requirements: pip install edge-tts SpeechRecognition pyaudio
Offline AI:   install Ollama (ollama.com) then: ollama pull tinyllama
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
import time
import tempfile

# ── Windows MCI audio player (built-in, no extra install) ────────────────────
_winmm = ctypes.windll.winmm

def _mci_play(path: str):
    """Play an MP3 using Windows MCI — blocks until done."""
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
    import pyttsx3
    PYTTSX = True
except ImportError:
    PYTTSX = False

try:
    import speech_recognition as sr
    SR = True
except ImportError:
    SR = False

# ── Theme ─────────────────────────────────────────────────────────────────────
BG      = "#000812"
PANEL   = "#00060f"
CYAN    = "#00d4ff"
BLUE    = "#0055cc"
DIM     = "#001f33"
GOLD    = "#ff8c00"
GREEN   = "#00ff88"
WHITE   = "#cceeff"
GRAY    = "#223344"

# ── AI config ─────────────────────────────────────────────────────────────────
OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "tinyllama"
VOICE        = "en-GB-RyanNeural"   # British male — closest to Jarvis

SYSTEM_PROMPT = (
    "You are J.A.R.V.I.S., Tony Stark's AI from Iron Man. "
    "Speak with intelligence, formality, and dry wit. "
    "Always address the user as 'sir'. "
    "Be concise — 1 to 3 sentences unless more detail is truly needed."
)


# ── Ollama backend ────────────────────────────────────────────────────────────
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
                "Please ensure Ollama is running and tinyllama is installed.")
    except Exception as e:
        return f"An error occurred in my language module, sir: {e}"


# ── HUD Canvas ────────────────────────────────────────────────────────────────
class HUD(tk.Canvas):
    STATES = {
        "idle":      CYAN,
        "listening": GREEN,
        "thinking":  GOLD,
        "speaking":  CYAN,
    }

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, highlightthickness=0, **kw)
        self.state  = "idle"
        self._tick  = 0

        self.after(100, self._loop)

    def set_state(self, s: str):
        self.state = s

    def _loop(self):
        self._draw()
        self._tick += 1
        self.after(33, self._loop)   # ~30 fps

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return

        cx = w // 2
        cy = h // 2
        t  = self._tick * 0.04
        col = self.STATES.get(self.state, CYAN)

        # ── Background hex grid (subtle) ──────────────────────────────────
        for gx in range(-w, w * 2, 60):
            for gy in range(-h, h * 2, 52):
                offset = 30 if (gy // 52) % 2 else 0
                self._hex(gx + offset, gy, 18, DIM)

        # ── Outer static ring + tick marks ───────────────────────────────
        R = min(cx, cy) - 18
        self.create_oval(cx-R, cy-R, cx+R, cy+R, outline=GRAY, width=1)
        for i in range(72):
            ang = math.radians(i * 5)
            ln  = 10 if i % 9 == 0 else (6 if i % 3 == 0 else 3)
            c2  = CYAN if i % 9 == 0 else (GRAY if i % 3 == 0 else DIM)
            x1  = cx + (R - ln) * math.cos(ang)
            y1  = cy + (R - ln) * math.sin(ang)
            x2  = cx + R * math.cos(ang)
            y2  = cy + R * math.sin(ang)
            self.create_line(x1, y1, x2, y2, fill=c2, width=1)

        # ── Rotating arc 1 — slow clockwise ──────────────────────────────
        r1 = R - 14
        a1 = (t * 25) % 360
        self.create_arc(cx-r1, cy-r1, cx+r1, cy+r1,
                        start=a1, extent=250, outline=CYAN, width=2, style="arc")

        # ── Rotating arc 2 — counter-clockwise ───────────────────────────
        r2 = R - 30
        a2 = (-t * 38) % 360
        self.create_arc(cx-r2, cy-r2, cx+r2, cy+r2,
                        start=a2, extent=170, outline=BLUE, width=2, style="arc")
        self.create_arc(cx-r2, cy-r2, cx+r2, cy+r2,
                        start=a2 + 200, extent=70, outline=BLUE, width=1, style="arc")

        # ── Rotating arc 3 — fast, state-colored ─────────────────────────
        r3 = R - 50
        a3 = (t * 65) % 360
        self.create_arc(cx-r3, cy-r3, cx+r3, cy+r3,
                        start=a3, extent=110, outline=col, width=3, style="arc")
        self.create_arc(cx-r3, cy-r3, cx+r3, cy+r3,
                        start=a3 + 160, extent=40, outline=col, width=1, style="arc")

        # ── Inner pulsing ring ────────────────────────────────────────────
        pulse = math.sin(t * (3 if self.state == "speaking" else 1.2)) * 0.5 + 0.5
        r4    = R - 72 + pulse * 6
        pw    = 1 + int(pulse * 3)
        ring_col = col if self.state != "idle" else DIM
        self.create_oval(cx-r4, cy-r4, cx+r4, cy+r4, outline=ring_col, width=pw)

        # ── Arc reactor centre ────────────────────────────────────────────
        rc = 22
        self.create_oval(cx-rc, cy-rc, cx+rc, cy+rc, outline=CYAN, width=2)
        # Triangle spokes
        for i in range(3):
            ang = math.radians(i * 120 - 90 + t * 15)
            x1i = cx + 6  * math.cos(ang)
            y1i = cy + 6  * math.sin(ang)
            x2i = cx + rc * math.cos(ang)
            y2i = cy + rc * math.sin(ang)
            self.create_line(x1i, y1i, x2i, y2i, fill=CYAN, width=2)
        # Centre dot
        ri = 5
        self.create_oval(cx-ri, cy-ri, cx+ri, cy+ri, fill=col, outline="")

        # ── HUD text labels ───────────────────────────────────────────────
        self.create_text(cx, cy - R - 14,
                         text="J.A.R.V.I.S.", fill=CYAN,
                         font=("Consolas", 13, "bold"), anchor="n")
        self.create_text(cx, cy + R + 5,
                         text=self.state.upper(), fill=col,
                         font=("Consolas", 9), anchor="n")
        self.create_text(18, cy,
                         text="STARK\nSYSTEMS", fill=GRAY,
                         font=("Consolas", 7), anchor="w")
        self.create_text(w - 18, cy,
                         text="AI\nCORE", fill=GRAY,
                         font=("Consolas", 7), anchor="e")

        # ── Waveform bars when active ─────────────────────────────────────
        if self.state in ("speaking", "listening"):
            bars    = 24
            bw      = 5
            spacing = 3
            total   = bars * (bw + spacing)
            bx0     = cx - total // 2
            speed   = 4 if self.state == "speaking" else 6
            for i in range(bars):
                bh = abs(math.sin(t * speed + i * 0.45)) * 22 + 4
                bx = bx0 + i * (bw + spacing)
                by = h - 10
                self.create_rectangle(bx, by - bh, bx + bw, by,
                                      fill=col, outline="")

    def _hex(self, x, y, r, color):
        pts = []
        for i in range(6):
            ang = math.radians(60 * i - 30)
            pts += [x + r * math.cos(ang), y + r * math.sin(ang)]
        self.create_polygon(pts, outline=color, fill="", width=1)


# ── Main app ──────────────────────────────────────────────────────────────────
class Jarvis:
    def __init__(self, root: tk.Tk):
        self.root      = root
        self.root.title("J.A.R.V.I.S.")
        self.root.configure(bg=BG)
        self.root.geometry("960x740")
        self.root.minsize(700, 560)

        self._speaking      = False
        self._mute_mic      = False
        self._history: list = []
        self._engine        = None

        self._init_tts()
        self._build_ui()
        self._start_always_on_mic()
        self.root.after(600, self._greet)

    # ── TTS ───────────────────────────────────────────────────────────────────
    def _init_tts(self):
        if PYTTSX:
            try:
                self._engine = pyttsx3.init()
                for v in self._engine.getProperty('voices'):
                    n = v.name.lower()
                    if any(x in n for x in ('david', 'george', 'mark', 'james')):
                        self._engine.setProperty('voice', v.id)
                        break
                self._engine.setProperty('rate', 148)
                self._engine.setProperty('volume', 1.0)
            except Exception:
                self._engine = None

    def _speak_worker(self, text: str):
        self._speaking = True
        self._mute_mic = True
        self._hud.set_state("speaking")
        try:
            if EDGE_TTS:
                asyncio.run(self._edge_speak(text))
            elif self._engine:
                self._engine.say(text)
                self._engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {e}")
        finally:
            self._speaking = False
            self._mute_mic = False
            self._hud.set_state("idle")

    async def _edge_speak(self, text: str):
        comm = edge_tts.Communicate(text, VOICE, rate="-8%", pitch="-10Hz")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            path = f.name
        await comm.save(path)
        await asyncio.get_event_loop().run_in_executor(None, _mci_play, path)
        try:
            os.unlink(path)
        except Exception:
            pass

    def speak(self, text: str):
        threading.Thread(target=self._speak_worker, args=(text,), daemon=True).start()

    # ── Always-on microphone ──────────────────────────────────────────────────
    def _start_always_on_mic(self):
        if not SR:
            self._append_sys("SpeechRecognition not installed — voice input disabled.")
            return
        try:
            rec = sr.Recognizer()
            rec.energy_threshold        = 350
            rec.dynamic_energy_threshold = True
            mic = sr.Microphone()

            with mic as src:
                rec.adjust_for_ambient_noise(src, duration=1.0)

            def on_speech(recognizer, audio):
                if self._mute_mic or self._speaking:
                    return
                self._hud.set_state("listening")
                try:
                    text = recognizer.recognize_google(audio).strip()
                    if text:
                        self.root.after(0, lambda t=text: self._on_input(t))
                except sr.UnknownValueError:
                    pass
                except Exception:
                    pass
                finally:
                    if not self._speaking:
                        self._hud.set_state("idle")

            rec.listen_in_background(mic, on_speech, phrase_time_limit=12)
            self._append_sys("Microphone active — just speak, sir.")
        except Exception as e:
            self._append_sys(f"Mic unavailable: {e}")

    # ── Process input ─────────────────────────────────────────────────────────
    def _on_input(self, text: str):
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
        # HUD
        self._hud = HUD(self.root, height=330)
        self._hud.pack(fill="x")

        # Cyan divider line
        tk.Frame(self.root, bg=CYAN, height=1).pack(fill="x")

        # Chat log
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
        self._chat.tag_config("sys",    foreground=GRAY,      font=("Consolas", 9,  "italic"))

        # Text input fallback row
        row = tk.Frame(self.root, bg="#000d1a", pady=8)
        row.pack(fill="x")

        self._entry = tk.Entry(
            row, bg="#001525", fg=WHITE, insertbackground=CYAN,
            font=("Consolas", 11), relief="flat",
            highlightthickness=1, highlightcolor=CYAN,
            highlightbackground=BLUE,
        )
        self._entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(16, 8))
        self._entry.bind("<Return>", lambda e: self._on_type())
        placeholder = "Speak freely — or type here and press Enter, sir."
        self._entry.insert(0, placeholder)
        self._entry.config(fg=GRAY)
        self._entry.bind("<FocusIn>",
            lambda e: (self._entry.delete(0, "end"),
                       self._entry.config(fg=WHITE))
            if self._entry.get() == placeholder else None)

        tk.Button(
            row, text="SEND", font=("Consolas", 10, "bold"),
            bg=CYAN, fg=BG, activebackground=WHITE, activeforeground=BG,
            relief="flat", padx=14, pady=5, command=self._on_type,
        ).pack(side="left", padx=(0, 16))

    def _on_type(self):
        text = self._entry.get().strip()
        if not text or "Speak freely" in text:
            return
        self._entry.delete(0, "end")
        self._on_input(text)

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
    if not EDGE_TTS:
        print("[JARVIS] For the best voice: pip install edge-tts")
    if not SR:
        print("[JARVIS] For voice input:    pip install SpeechRecognition pyaudio")
    print("[JARVIS] For offline AI:     install Ollama then: ollama pull tinyllama")

    root = tk.Tk()
    Jarvis(root)
    root.mainloop()
