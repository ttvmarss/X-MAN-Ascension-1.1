import tkinter as tk
import tkinter.font as tkfont
import threading
import time
import os
import subprocess
import sys

try:
    import pyttsx3
    TTS_OK = True
except ImportError:
    TTS_OK = False

try:
    import speech_recognition as sr
    SR_OK = True
except ImportError:
    SR_OK = False

try:
    from groq import Groq
    GROQ_OK = True
except ImportError:
    GROQ_OK = False

# ── Colors ──────────────────────────────────────────────────────────────────
BG       = "#020b18"
PANEL    = "#041525"
ACCENT   = "#00cfff"
GOLD     = "#c8922a"
GREEN    = "#00ff88"
DIM      = "#1a3a4a"
TEXT     = "#b8e8ff"
WHITE    = "#e8f8ff"

GROQ_MODEL = "llama3-70b-8192"
SYSTEM_PROMPT = (
    "You are J.A.R.V.I.S., the AI assistant from Iron Man. "
    "You are highly intelligent, witty, and speak formally with subtle dry humor. "
    "Always address the user as 'sir'. "
    "Keep responses concise — 1-3 sentences unless a longer answer is truly needed. "
    "You assist with any task the user requests."
)


class Jarvis:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("J.A.R.V.I.S.")
        self.root.configure(bg=BG)
        self.root.geometry("820x640")
        self.root.minsize(640, 480)

        self._listening = False
        self._speaking = False
        self._anim_idx = 0
        self._history: list[dict] = []

        self._init_tts()
        self._init_groq()
        self._build_ui()
        self._animate()
        self._greet()

    # ── TTS ─────────────────────────────────────────────────────────────────

    def _init_tts(self):
        if not TTS_OK:
            self._engine = None
            return
        try:
            self._engine = pyttsx3.init()
            voices = self._engine.getProperty('voices')
            # prefer a lower-pitched male voice for Jarvis feel
            chosen = None
            for v in voices:
                name = v.name.lower()
                if 'david' in name or 'mark' in name or 'james' in name:
                    chosen = v.id
                    break
            if chosen:
                self._engine.setProperty('voice', chosen)
            self._engine.setProperty('rate', 160)
            self._engine.setProperty('volume', 1.0)
        except Exception:
            self._engine = None

    def _speak(self, text: str):
        if not self._engine:
            return
        self._speaking = True
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception:
            pass
        finally:
            self._speaking = False

    def speak_async(self, text: str):
        threading.Thread(target=self._speak, args=(text,), daemon=True).start()

    # ── Groq AI ─────────────────────────────────────────────────────────────

    def _init_groq(self):
        self._groq = None
        if not GROQ_OK:
            return
        key = os.environ.get("GROQ_API_KEY", "")
        if key:
            try:
                self._groq = Groq(api_key=key)
            except Exception:
                pass

    def _ask_ai(self, user_text: str) -> str:
        if not self._groq:
            return "I'm afraid the AI module is offline, sir. Set GROQ_API_KEY to enable it."
        self._history.append({"role": "user", "content": user_text})
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self._history[-20:]
        try:
            resp = self._groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                max_tokens=300,
                temperature=0.7,
            )
            reply = resp.choices[0].message.content.strip()
            self._history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            return f"I encountered an error, sir: {e}"

    # ── Speech Recognition ───────────────────────────────────────────────────

    def _listen_microphone(self):
        if not SR_OK:
            self._set_status("speech_recognition not installed, sir.", GOLD)
            return
        self._set_status("Listening…", GREEN)
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, timeout=8, phrase_time_limit=15)
            text = r.recognize_google(audio)
            self._on_user_input(text)
        except sr.WaitTimeoutError:
            self._set_status("No speech detected, sir.", GOLD)
        except sr.UnknownValueError:
            self._set_status("I didn't catch that, sir.", GOLD)
        except Exception as e:
            self._set_status(f"Error: {e}", GOLD)
        finally:
            self._listening = False
            self.root.after(0, lambda: self._mic_btn.config(state="normal"))

    def start_listening(self):
        if self._listening:
            return
        self._listening = True
        self._mic_btn.config(state="disabled")
        threading.Thread(target=self._listen_microphone, daemon=True).start()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=PANEL, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="J.A.R.V.I.S.", font=("Consolas", 22, "bold"),
                 fg=ACCENT, bg=PANEL).pack(side="left", padx=20, pady=14)

        self._status_lbl = tk.Label(hdr, text="ONLINE", font=("Consolas", 10),
                                    fg=GREEN, bg=PANEL)
        self._status_lbl.pack(side="left", padx=0, pady=14)

        tk.Label(hdr, text="IRON MAN SYSTEM  ●  GROQ FREE TIER",
                 font=("Consolas", 9), fg=DIM, bg=PANEL).pack(side="right", padx=20)

        # ── Arc-reactor decoration strip ────────────────────────────────────
        strip = tk.Frame(self.root, bg=ACCENT, height=2)
        strip.pack(fill="x")

        # ── Conversation area ────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=(12, 0))

        self._chat = tk.Text(
            body, bg=PANEL, fg=TEXT, font=("Consolas", 11),
            relief="flat", padx=14, pady=10, wrap="word",
            state="disabled", borderwidth=0,
            selectbackground=DIM, selectforeground=WHITE,
        )
        sb = tk.Scrollbar(body, command=self._chat.yview, bg=BG, troughcolor=PANEL,
                          activebackground=ACCENT, relief="flat")
        self._chat.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._chat.pack(fill="both", expand=True)

        self._chat.tag_config("you",    foreground=GOLD,  font=("Consolas", 11, "bold"))
        self._chat.tag_config("jarvis", foreground=ACCENT, font=("Consolas", 11, "bold"))
        self._chat.tag_config("msg",    foreground=TEXT,   font=("Consolas", 11))
        self._chat.tag_config("dim",    foreground=DIM,    font=("Consolas", 9))

        # ── Input row ────────────────────────────────────────────────────────
        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="x", padx=16, pady=10)

        self._entry = tk.Entry(
            row, bg=PANEL, fg=WHITE, insertbackground=ACCENT,
            font=("Consolas", 12), relief="flat",
            highlightthickness=1, highlightcolor=ACCENT,
            highlightbackground=DIM,
        )
        self._entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self._entry.bind("<Return>", lambda e: self._on_send())

        self._mic_btn = tk.Button(
            row, text="🎙", font=("Consolas", 14),
            bg=DIM, fg=WHITE, activebackground=ACCENT, activeforeground=BG,
            relief="flat", padx=10, command=self.start_listening,
        )
        self._mic_btn.pack(side="left", ipady=4)

        send_btn = tk.Button(
            row, text="SEND", font=("Consolas", 11, "bold"),
            bg=ACCENT, fg=BG, activebackground=WHITE, activeforeground=BG,
            relief="flat", padx=16, command=self._on_send,
        )
        send_btn.pack(side="left", padx=(8, 0), ipady=4)

        # ── Footer ────────────────────────────────────────────────────────────
        ftr = tk.Frame(self.root, bg=PANEL, height=28)
        ftr.pack(fill="x")
        ftr.pack_propagate(False)
        self._anim_lbl = tk.Label(ftr, text="● ● ●", font=("Consolas", 9),
                                  fg=DIM, bg=PANEL)
        self._anim_lbl.pack(side="left", padx=16, pady=6)
        tk.Label(ftr, text="X-MAN ASCENSION  v2.0",
                 font=("Consolas", 9), fg=DIM, bg=PANEL).pack(side="right", padx=16)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _set_status(self, text: str, color: str = GREEN):
        self.root.after(0, lambda: self._status_lbl.config(text=text, fg=color))

    def _append_chat(self, speaker: str, message: str):
        self._chat.config(state="normal")
        if self._chat.index("end-1c") != "1.0":
            self._chat.insert("end", "\n")
        tag = "you" if speaker == "YOU" else "jarvis"
        self._chat.insert("end", f"{speaker}: ", tag)
        self._chat.insert("end", message + "\n", "msg")
        self._chat.see("end")
        self._chat.config(state="disabled")

    def _on_send(self):
        text = self._entry.get().strip()
        if not text:
            return
        self._entry.delete(0, "end")
        self._on_user_input(text)

    def _on_user_input(self, text: str):
        self._append_chat("YOU", text)
        self._set_status("Thinking…", ACCENT)
        threading.Thread(target=self._process, args=(text,), daemon=True).start()

    def _process(self, text: str):
        reply = self._ask_ai(text)
        self.root.after(0, lambda: self._append_chat("JARVIS", reply))
        self._set_status("Ready, sir.", GREEN)
        self.speak_async(reply)

    def _greet(self):
        greeting = "Good day, sir. J.A.R.V.I.S. is fully operational and at your service."
        self._append_chat("JARVIS", greeting)
        self.speak_async(greeting)

    def _animate(self):
        frames = [
            ("▶ ◀ ● ◀ ▶", ACCENT),
            ("◀ ▶ ● ▶ ◀", DIM),
            ("● ◀ ▶ ◀ ●", ACCENT),
            ("▶ ● ◀ ● ▶", DIM),
        ]
        f_text, f_color = frames[self._anim_idx % len(frames)]
        if self._speaking:
            f_color = GOLD
        elif self._listening:
            f_color = GREEN
        self._anim_lbl.config(text=f_text, fg=f_color)
        self._anim_idx += 1
        self.root.after(500, self._animate)


def check_deps():
    missing = []
    if not TTS_OK:
        missing.append("pyttsx3")
    if not SR_OK:
        missing.append("SpeechRecognition")
    if not GROQ_OK:
        missing.append("groq")
    if missing:
        print(f"[JARVIS] Optional packages not installed: {', '.join(missing)}")
        print(f"[JARVIS] Install with: pip install {' '.join(missing)}")
    if not GROQ_OK or not os.environ.get("GROQ_API_KEY"):
        print("[JARVIS] Set GROQ_API_KEY environment variable for AI responses.")


if __name__ == "__main__":
    check_deps()
    root = tk.Tk()
    app = Jarvis(root)
    root.mainloop()
