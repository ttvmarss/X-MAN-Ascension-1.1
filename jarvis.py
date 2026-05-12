import tkinter as tk
import threading
import os
import urllib.request
import urllib.error
import json

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

# ── Colors ────────────────────────────────────────────────────────────────
BG     = "#020b18"
PANEL  = "#041525"
ACCENT = "#00cfff"
GOLD   = "#c8922a"
GREEN  = "#00ff88"
DIM    = "#1a3a4a"
TEXT   = "#b8e8ff"
WHITE  = "#e8f8ff"

OLLAMA_URL  = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "tinyllama"  # small & fast; swap for llama3 if you have it

SYSTEM_PROMPT = (
    "You are J.A.R.V.I.S., the AI assistant from Iron Man. "
    "You are highly intelligent, witty, and speak formally with subtle dry humor. "
    "Always address the user as 'sir'. "
    "Keep responses concise — 1-3 sentences unless more is truly needed."
)

FALLBACK_REPLIES = [
    "I'm afraid my neural core is offline, sir. Please install Ollama to restore full AI capability.",
    "Running on backup systems only, sir. Install Ollama for full intelligence.",
    "AI module unavailable, sir. See the setup instructions below.",
]
_fb_idx = 0


def _fallback_reply() -> str:
    global _fb_idx
    r = FALLBACK_REPLIES[_fb_idx % len(FALLBACK_REPLIES)]
    _fb_idx += 1
    return r


def ask_ollama(history: list[dict]) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-20:]
    body = json.dumps({"model": OLLAMA_MODEL, "messages": messages, "stream": False}).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=body,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["message"]["content"].strip()
    except urllib.error.URLError:
        return _fallback_reply()
    except Exception as e:
        return f"Error communicating with Ollama, sir: {e}"


class Jarvis:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("J.A.R.V.I.S.")
        self.root.configure(bg=BG)
        self.root.geometry("820x640")
        self.root.minsize(640, 480)

        self._listening = False
        self._speaking  = False
        self._anim_idx  = 0
        self._history: list[dict] = []

        self._init_tts()
        self._build_ui()
        self._animate()
        self._greet()

    # ── TTS ──────────────────────────────────────────────────────────────

    def _init_tts(self):
        if not TTS_OK:
            self._engine = None
            return
        try:
            self._engine = pyttsx3.init()
            for v in self._engine.getProperty('voices'):
                if any(n in v.name.lower() for n in ('david', 'mark', 'james', 'george')):
                    self._engine.setProperty('voice', v.id)
                    break
            self._engine.setProperty('rate', 155)
            self._engine.setProperty('volume', 1.0)
        except Exception:
            self._engine = None

    def _speak_worker(self, text: str):
        self._speaking = True
        try:
            if self._engine:
                self._engine.say(text)
                self._engine.runAndWait()
        except Exception:
            pass
        finally:
            self._speaking = False

    def speak_async(self, text: str):
        threading.Thread(target=self._speak_worker, args=(text,), daemon=True).start()

    # ── Mic ──────────────────────────────────────────────────────────────

    def _listen_worker(self):
        self._set_status("Listening…", GREEN)
        r = sr.Recognizer()
        try:
            with sr.Microphone() as src:
                r.adjust_for_ambient_noise(src, duration=0.4)
                audio = r.listen(src, timeout=8, phrase_time_limit=15)
            text = r.recognize_google(audio)
            self._on_user_input(text)
        except sr.WaitTimeoutError:
            self._set_status("No speech detected, sir.", GOLD)
        except sr.UnknownValueError:
            self._set_status("Didn't catch that, sir.", GOLD)
        except Exception as e:
            self._set_status(f"Mic error: {e}", GOLD)
        finally:
            self._listening = False
            self.root.after(0, lambda: self._mic_btn.config(state="normal"))

    def start_listening(self):
        if self._listening or not SR_OK:
            return
        self._listening = True
        self._mic_btn.config(state="disabled")
        threading.Thread(target=self._listen_worker, daemon=True).start()

    # ── UI ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=PANEL, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="J.A.R.V.I.S.", font=("Consolas", 22, "bold"),
                 fg=ACCENT, bg=PANEL).pack(side="left", padx=20, pady=14)
        self._status_lbl = tk.Label(hdr, text="ONLINE", font=("Consolas", 10),
                                    fg=GREEN, bg=PANEL)
        self._status_lbl.pack(side="left")
        tk.Label(hdr, text="OFFLINE AI  ●  NO KEY REQUIRED",
                 font=("Consolas", 9), fg=DIM, bg=PANEL).pack(side="right", padx=20)

        # Arc strip
        tk.Frame(self.root, bg=ACCENT, height=2).pack(fill="x")

        # Chat area
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=(12, 0))
        self._chat = tk.Text(body, bg=PANEL, fg=TEXT, font=("Consolas", 11),
                             relief="flat", padx=14, pady=10, wrap="word",
                             state="disabled", borderwidth=0,
                             selectbackground=DIM, selectforeground=WHITE)
        sb = tk.Scrollbar(body, command=self._chat.yview, bg=BG,
                          troughcolor=PANEL, activebackground=ACCENT, relief="flat")
        self._chat.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._chat.pack(fill="both", expand=True)
        self._chat.tag_config("you",    foreground=GOLD,  font=("Consolas", 11, "bold"))
        self._chat.tag_config("jarvis", foreground=ACCENT, font=("Consolas", 11, "bold"))
        self._chat.tag_config("msg",    foreground=TEXT,   font=("Consolas", 11))
        self._chat.tag_config("sys",    foreground=DIM,    font=("Consolas", 9, "italic"))

        # Input row
        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="x", padx=16, pady=10)
        self._entry = tk.Entry(row, bg=PANEL, fg=WHITE, insertbackground=ACCENT,
                               font=("Consolas", 12), relief="flat",
                               highlightthickness=1, highlightcolor=ACCENT,
                               highlightbackground=DIM)
        self._entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self._entry.bind("<Return>", lambda e: self._on_send())

        self._mic_btn = tk.Button(row, text="🎙", font=("Consolas", 14),
                                  bg=DIM, fg=WHITE, activebackground=GREEN,
                                  activeforeground=BG, relief="flat", padx=10,
                                  command=self.start_listening,
                                  state="normal" if SR_OK else "disabled")
        self._mic_btn.pack(side="left")

        tk.Button(row, text="SEND", font=("Consolas", 11, "bold"),
                  bg=ACCENT, fg=BG, activebackground=WHITE,
                  relief="flat", padx=16, command=self._on_send
                  ).pack(side="left", padx=(8, 0), ipady=4)

        # Footer
        ftr = tk.Frame(self.root, bg=PANEL, height=28)
        ftr.pack(fill="x")
        ftr.pack_propagate(False)
        self._anim_lbl = tk.Label(ftr, text="● ● ●", font=("Consolas", 9),
                                  fg=DIM, bg=PANEL)
        self._anim_lbl.pack(side="left", padx=16, pady=6)
        tk.Label(ftr, text="X-MAN ASCENSION  v2.0  ●  POWERED BY OLLAMA",
                 font=("Consolas", 9), fg=DIM, bg=PANEL).pack(side="right", padx=16)

    # ── Helpers ──────────────────────────────────────────────────────────

    def _set_status(self, text: str, color: str = GREEN):
        self.root.after(0, lambda: self._status_lbl.config(text=text, fg=color))

    def _append(self, speaker: str, message: str, tag: str = "msg"):
        self._chat.config(state="normal")
        if self._chat.index("end-1c") != "1.0":
            self._chat.insert("end", "\n")
        sp_tag = "you" if speaker == "YOU" else "jarvis" if speaker == "JARVIS" else "sys"
        if speaker:
            self._chat.insert("end", f"{speaker}: ", sp_tag)
        self._chat.insert("end", message + "\n", tag)
        self._chat.see("end")
        self._chat.config(state="disabled")

    def _on_send(self):
        text = self._entry.get().strip()
        if not text:
            return
        self._entry.delete(0, "end")
        self._on_user_input(text)

    def _on_user_input(self, text: str):
        self._append("YOU", text)
        self._set_status("Thinking…", ACCENT)
        self._history.append({"role": "user", "content": text})
        threading.Thread(target=self._process, daemon=True).start()

    def _process(self):
        reply = ask_ollama(self._history)
        self._history.append({"role": "assistant", "content": reply})
        self.root.after(0, lambda: self._append("JARVIS", reply))
        self._set_status("Ready, sir.", GREEN)
        self.speak_async(reply)

    def _greet(self):
        msg = "Good day, sir. J.A.R.V.I.S. is online and at your service."
        self._append("JARVIS", msg)
        # show setup tip if Ollama likely not running
        self._append("", "Tip: install Ollama (ollama.com) and run: ollama pull tinyllama", "sys")
        self.speak_async(msg)

    def _animate(self):
        frames = [("▶ ◀ ● ◀ ▶", ACCENT), ("◀ ▶ ● ▶ ◀", DIM),
                  ("● ◀ ▶ ◀ ●", ACCENT), ("▶ ● ◀ ● ▶", DIM)]
        txt, col = frames[self._anim_idx % len(frames)]
        if self._speaking:  col = GOLD
        elif self._listening: col = GREEN
        self._anim_lbl.config(text=txt, fg=col)
        self._anim_idx += 1
        self.root.after(500, self._animate)


if __name__ == "__main__":
    root = tk.Tk()
    Jarvis(root)
    root.mainloop()
