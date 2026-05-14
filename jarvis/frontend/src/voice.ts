/**
 * Voice input (Web Speech API) and audio output (AudioContext) for JARVIS.
 */

// ---------------------------------------------------------------------------
// Speech Recognition
// ---------------------------------------------------------------------------

export interface VoiceInput {
  start(): void;
  stop(): void;
  pause(): void;
  resume(): void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare const webkitSpeechRecognition: any;

export function createVoiceInput(
  onTranscript: (text: string) => void,
  onError: (msg: string) => void,
  onInterimSpeech?: () => void,  // Called when user starts speaking (enables barge-in)
): VoiceInput {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const SR = (window as any).SpeechRecognition || (typeof webkitSpeechRecognition !== "undefined" ? webkitSpeechRecognition : null);
  if (!SR) {
    onError("Speech recognition not supported. Please use Chrome or Edge.");
    return { start() {}, stop() {}, pause() {}, resume() {} };
  }

  const recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en-US";
  recognition.maxAlternatives = 1;

  let shouldListen = false;
  let paused = false;
  let interimFired = false;
  let restartTimer: ReturnType<typeof setTimeout> | null = null;

  recognition.onresult = (event: any) => {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i];
      if (!result.isFinal) {
        // Interim = user is actively speaking — fire barge-in once per utterance
        if (!interimFired && onInterimSpeech) {
          interimFired = true;
          onInterimSpeech();
        }
      } else {
        interimFired = false;
        const text = result[0].transcript.trim();
        // Ignore noise/empty captures
        if (text && text.length > 1) {
          onTranscript(text);
        }
      }
    }
  };

  recognition.onend = () => {
    if (shouldListen && !paused) {
      // Short delay before restart to prevent rapid-fire loop
      restartTimer = setTimeout(() => {
        if (shouldListen && !paused) {
          try { recognition.start(); } catch { /* already started */ }
        }
      }, 150);
    }
  };

  recognition.onerror = (event: any) => {
    if (event.error === "not-allowed") {
      onError("Microphone access denied — allow mic access in browser settings.");
      shouldListen = false;
    } else if (event.error === "no-speech" || event.error === "aborted") {
      // Normal — recognition will end and restart via onend
    } else {
      console.warn("[voice] recognition error:", event.error);
    }
  };

  return {
    start() {
      shouldListen = true;
      paused = false;
      interimFired = false;
      try { recognition.start(); } catch { /* already started */ }
    },
    stop() {
      shouldListen = false;
      paused = false;
      if (restartTimer) { clearTimeout(restartTimer); restartTimer = null; }
      try { recognition.stop(); } catch { /* already stopped */ }
    },
    pause() {
      paused = true;
      if (restartTimer) { clearTimeout(restartTimer); restartTimer = null; }
      try { recognition.stop(); } catch { /* already stopped */ }
    },
    resume() {
      paused = false;
      interimFired = false;
      if (shouldListen) {
        try { recognition.start(); } catch { /* already started */ }
      }
    },
  };
}

// ---------------------------------------------------------------------------
// Audio Player
// ---------------------------------------------------------------------------

export interface AudioPlayer {
  enqueue(base64: string): Promise<void>;
  stop(): void;
  getAnalyser(): AnalyserNode;
  onFinished(cb: () => void): void;
}

export function createAudioPlayer(): AudioPlayer {
  const audioCtx = new AudioContext();
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 256;
  analyser.smoothingTimeConstant = 0.8;
  analyser.connect(audioCtx.destination);

  const queue: AudioBuffer[] = [];
  let isPlaying = false;
  let currentSource: AudioBufferSourceNode | null = null;
  let finishedCallback: (() => void) | null = null;
  let stopped = false;  // Set true during stop() to prevent onended firing

  function playNext() {
    if (stopped || queue.length === 0) {
      isPlaying = false;
      currentSource = null;
      if (!stopped) finishedCallback?.();
      return;
    }

    isPlaying = true;
    const buffer = queue.shift()!;
    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(analyser);
    currentSource = source;

    source.onended = () => {
      if (currentSource === source && !stopped) {
        playNext();
      }
    };

    source.start();
  }

  return {
    async enqueue(base64: string) {
      stopped = false;
      // Resume audio context (browser autoplay policy)
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }

      try {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
          bytes[i] = binary.charCodeAt(i);
        }
        const audioBuffer = await audioCtx.decodeAudioData(bytes.buffer.slice(0));
        queue.push(audioBuffer);
        if (!isPlaying) playNext();
      } catch (err) {
        console.error("[audio] decode error:", err);
        if (!isPlaying && queue.length > 0) playNext();
      }
    },

    stop() {
      stopped = true;
      queue.length = 0;
      if (currentSource) {
        try { currentSource.stop(); } catch { /* already stopped */ }
        currentSource = null;
      }
      isPlaying = false;
    },

    getAnalyser() {
      return analyser;
    },

    onFinished(cb: () => void) {
      finishedCallback = cb;
    },
  };
}
