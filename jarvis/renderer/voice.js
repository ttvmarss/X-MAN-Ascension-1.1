/**
 * Voice input (SpeechRecognition) and output (SpeechSynthesis).
 */

class VoiceController {
  constructor({ onStateChange, onTranscript, onError }) {
    this.onStateChange = onStateChange;
    this.onTranscript = onTranscript;
    this.onError = onError;
    this.muted = false;
    this.listening = false;
    this.speaking = false;
    this.wakePhraseRequired = true;
    this.recognition = null;
    this.preferredVoice = null;
    this._restartTimer = null;
    this._initRecognition();
    this._initSynthesis();
  }

  _initRecognition() {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      this.onError?.("Speech recognition is not supported in this environment.");
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = "en-US";
    this.recognition.maxAlternatives = 1;

    this.recognition.onstart = () => {
      this.listening = true;
      if (!this.speaking) {
        this.onStateChange?.("listening");
      }
    };

    this.recognition.onend = () => {
      this.listening = false;
      if (!this.muted && !this.speaking) {
        this._scheduleRestart();
      }
      if (!this.speaking) {
        this.onStateChange?.("idle");
      }
    };

    this.recognition.onerror = (event) => {
      if (event.error === "no-speech" || event.error === "aborted") {
        return;
      }
      if (event.error === "not-allowed") {
        this.onError?.("Microphone access was denied. Please allow microphone permission.");
        this.muted = true;
        return;
      }
      console.warn("[voice] recognition error:", event.error);
      if (!this.muted) {
        this._scheduleRestart(800);
      }
    };

    this.recognition.onresult = (event) => {
      let finalText = "";
      let interim = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const text = result[0].transcript.trim();
        if (result.isFinal) {
          finalText += (finalText ? " " : "") + text;
        } else {
          interim = text;
        }
      }

      if (interim && !this.speaking) {
        this.onStateChange?.("listening");
      }

      if (finalText) {
        const processed = this._maybeStripWakePhrase(finalText);
        if (processed !== null) {
          this.onTranscript?.(processed);
        }
      }
    };
  }

  _initSynthesis() {
    if (!window.speechSynthesis) {
      this.onError?.("Speech synthesis is not supported in this environment.");
      return;
    }

    const pickVoice = () => {
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(
        (v) =>
          v.lang.startsWith("en") &&
          (/natural|neural|premium|online/i.test(v.name) ||
            /Microsoft .* Natural|Google US English/i.test(v.name))
      );
      const english = voices.find((v) => v.lang.startsWith("en"));
      this.preferredVoice = preferred || english || voices[0] || null;
    };

    pickVoice();
    window.speechSynthesis.onvoiceschanged = pickVoice;
  }

  _maybeStripWakePhrase(text) {
    const lower = text.toLowerCase();
    const triggers = ["hey jarvis", "ok jarvis", "jarvis"];
    for (const trigger of triggers) {
      if (lower.startsWith(trigger)) {
        const rest = text.slice(trigger.length).replace(/^[,.\s]+/, "").trim();
        return rest || "hello";
      }
      if (lower.includes(trigger)) {
        const idx = lower.indexOf(trigger);
        const rest = text.slice(idx + trigger.length).replace(/^[,.\s]+/, "").trim();
        if (rest) return rest;
      }
    }
    if (this.wakePhraseRequired) {
      return null;
    }
    return text;
  }

  _scheduleRestart(delay = 300) {
    clearTimeout(this._restartTimer);
    this._restartTimer = setTimeout(() => {
      if (!this.muted && !this.speaking) {
        this.startListening();
      }
    }, delay);
  }

  startListening() {
    if (!this.recognition || this.muted || this.speaking) return;
    try {
      this.recognition.start();
    } catch {
      // Already started
    }
  }

  stopListening() {
    clearTimeout(this._restartTimer);
    if (!this.recognition) return;
    try {
      this.recognition.stop();
    } catch {
      // ignore
    }
  }

  setMuted(muted) {
    this.muted = muted;
    if (muted) {
      this.stopListening();
      if (!this.speaking) {
        this.onStateChange?.("idle");
      }
    } else {
      this.startListening();
    }
  }

  /**
   * Speak text aloud. Returns a promise that resolves when done.
   */
  speak(text, { onPulse } = {}) {
    return new Promise((resolve, reject) => {
      if (!window.speechSynthesis) {
        reject(new Error("Speech synthesis unavailable"));
        return;
      }

      this.speaking = true;
      this.stopListening();
      this.onStateChange?.("speaking");

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.92;
      utterance.pitch = 0.95;
      utterance.volume = 1;
      if (this.preferredVoice) {
        utterance.voice = this.preferredVoice;
      }

      let pulseTimer = null;
      if (onPulse) {
        pulseTimer = setInterval(() => {
          onPulse(0.4 + Math.random() * 0.5);
        }, 120);
      }

      utterance.onboundary = () => {
        onPulse?.(0.5 + Math.random() * 0.4);
      };

      utterance.onend = () => {
        clearInterval(pulseTimer);
        onPulse?.(0);
        this.speaking = false;
        this.onStateChange?.("idle");
        if (!this.muted) {
          this._scheduleRestart(400);
        }
        resolve();
      };

      utterance.onerror = (event) => {
        clearInterval(pulseTimer);
        onPulse?.(0);
        this.speaking = false;
        this.onStateChange?.("idle");
        if (!this.muted) {
          this._scheduleRestart(400);
        }
        if (event.error !== "interrupted") {
          reject(new Error(event.error || "speech error"));
        } else {
          resolve();
        }
      };

      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    });
  }

  cancelSpeech() {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    this.speaking = false;
  }
}

window.VoiceController = VoiceController;
