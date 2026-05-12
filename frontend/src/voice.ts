/**
 * Voice module: dual-mode speech recognition + TTS playback.
 *
 * Desktop Chrome: Web Speech API (continuous, hands-free).
 * iOS Safari / push-to-talk: MediaRecorder → server /api/transcribe (Whisper).
 *
 * iOS Safari's webkitSpeechRecognition is unreliable, so we use MediaRecorder
 * instead and POST the audio blob to the backend for transcription.
 */

export type VoiceState = 'idle' | 'listening' | 'recording' | 'processing' | 'speaking'
export type VoiceMode = 'continuous' | 'push_to_talk'

export interface VoiceCallbacks {
  onTranscript: (text: string, final: boolean) => void
  onStateChange: (state: VoiceState) => void
  onAudioLevel: (level: number) => void
}

export function detectMode(): VoiceMode {
  const ua = navigator.userAgent
  const isIOS = /iPad|iPhone|iPod/.test(ua) && !(window as any).MSStream
  const isSafari = /^((?!chrome|android).)*safari/i.test(ua)
  const hasWebSpeech = 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window
  if (isIOS || isSafari || !hasWebSpeech) return 'push_to_talk'
  return 'continuous'
}

export class VoiceManager {
  private mode: VoiceMode
  private recognition: SpeechRecognition | null = null
  private audioCtx: AudioContext | null = null
  private analyser: AnalyserNode | null = null
  private micStream: MediaStream | null = null
  private state: VoiceState = 'idle'
  private callbacks: VoiceCallbacks
  private audioQueue: ArrayBuffer[] = []
  private isPlayingAudio: boolean = false
  private activeAudio: HTMLAudioElement | null = null
  private levelTimer: number = 0

  // MediaRecorder state for iOS path
  private recorder: MediaRecorder | null = null
  private recordedChunks: Blob[] = []

  constructor(callbacks: VoiceCallbacks, mode?: VoiceMode) {
    this.callbacks = callbacks
    this.mode = mode || detectMode()
  }

  getMode(): VoiceMode {
    return this.mode
  }

  async init(): Promise<void> {
    await this._initAudioContext()
    if (this.mode === 'continuous') {
      this._initSpeechRecognition()
    }
  }

  private async _initAudioContext(): Promise<void> {
    try {
      this.audioCtx = new AudioContext()
      this.micStream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
        video: false,
      })
      const source = this.audioCtx.createMediaStreamSource(this.micStream)
      this.analyser = this.audioCtx.createAnalyser()
      this.analyser.fftSize = 256
      source.connect(this.analyser)
      this._startLevelPolling()
    } catch (e) {
      console.error('Microphone access denied or unavailable:', e)
      throw e
    }
  }

  private _startLevelPolling(): void {
    if (!this.analyser) return
    const data = new Uint8Array(this.analyser.frequencyBinCount)
    const tick = () => {
      this.levelTimer = requestAnimationFrame(tick)
      if (!this.analyser) return
      this.analyser.getByteFrequencyData(data)
      let sum = 0
      for (let i = 0; i < data.length; i++) sum += data[i]
      this.callbacks.onAudioLevel(sum / data.length / 255)
    }
    tick()
  }

  private _initSpeechRecognition(): void {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SR) {
      console.warn('Web Speech API not available; falling back to push-to-talk.')
      this.mode = 'push_to_talk'
      return
    }
    this.recognition = new SR()
    this.recognition.continuous = true
    this.recognition.interimResults = true
    this.recognition.lang = 'en-US'

    this.recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = ''
      let finalText = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const r = event.results[i]
        if (r.isFinal) finalText += r[0].transcript
        else interim += r[0].transcript
      }
      if (interim) this.callbacks.onTranscript(interim, false)
      if (finalText.trim()) this.callbacks.onTranscript(finalText.trim(), true)
    }

    this.recognition.onerror = (e: SpeechRecognitionErrorEvent) => {
      if (e.error === 'no-speech' || e.error === 'aborted') return
      console.warn('SR error:', e.error)
    }

    this.recognition.onend = () => {
      if (this.state === 'listening') {
        setTimeout(() => {
          try { this.recognition?.start() } catch {}
        }, 300)
      }
    }
  }

  /** Continuous-mode: start listening. No-op in push-to-talk. */
  startListening(): void {
    if (this.mode !== 'continuous' || !this.recognition) return
    this._setState('listening')
    try { this.recognition.start() } catch {}
  }

  stopListening(): void {
    if (this.recognition) {
      try { this.recognition.stop() } catch {}
    }
  }

  /** Push-to-talk: begin recording audio. */
  async startRecording(): Promise<void> {
    if (!this.micStream) return
    this.recordedChunks = []
    const mimeType = this._pickMimeType()
    try {
      this.recorder = new MediaRecorder(this.micStream, { mimeType })
    } catch {
      this.recorder = new MediaRecorder(this.micStream)
    }
    this.recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) this.recordedChunks.push(e.data)
    }
    this.recorder.start()
    this._setState('recording')
  }

  /** Push-to-talk: stop recording, transcribe, return text via callback. */
  async stopRecording(transcribeUrl: string): Promise<void> {
    if (!this.recorder) return
    const recorder = this.recorder
    this.recorder = null

    await new Promise<void>((resolve) => {
      recorder.onstop = () => resolve()
      try { recorder.stop() } catch { resolve() }
    })

    if (this.recordedChunks.length === 0) {
      this._setState('idle')
      return
    }

    const blob = new Blob(this.recordedChunks, { type: this.recordedChunks[0].type || 'audio/webm' })
    this.recordedChunks = []
    this._setState('processing')

    try {
      const resp = await fetch(transcribeUrl, {
        method: 'POST',
        headers: { 'Content-Type': blob.type },
        body: blob,
      })
      if (!resp.ok) {
        console.error('Transcribe failed:', resp.status)
        this._setState('idle')
        return
      }
      const data = await resp.json()
      const text = (data.text || '').trim()
      if (text) {
        this.callbacks.onTranscript(text, true)
      } else {
        this._setState('idle')
      }
    } catch (e) {
      console.error('Transcribe error:', e)
      this._setState('idle')
    }
  }

  private _pickMimeType(): string {
    const candidates = [
      'audio/mp4',           // iOS Safari
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
    ]
    for (const m of candidates) {
      if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(m)) return m
    }
    return ''
  }

  async playAudioBuffer(buffer: ArrayBuffer): Promise<void> {
    this.audioQueue.push(buffer)
    if (!this.isPlayingAudio) await this._drainQueue()
  }

  private async _drainQueue(): Promise<void> {
    while (this.audioQueue.length > 0) {
      const buf = this.audioQueue.shift()!
      await this._playOnce(buf)
    }
    if (this.mode === 'continuous') {
      this._setState('listening')
      this.startListening()
    } else {
      this._setState('idle')
    }
  }

  private _playOnce(buffer: ArrayBuffer): Promise<void> {
    return new Promise((resolve) => {
      this.isPlayingAudio = true
      this._setState('speaking')

      const blob = new Blob([buffer], { type: 'audio/mpeg' })
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      this.activeAudio = audio

      const done = () => {
        URL.revokeObjectURL(url)
        this.isPlayingAudio = false
        this.activeAudio = null
        resolve()
      }
      audio.onended = done
      audio.onerror = done
      audio.play().catch(done)
    })
  }

  stopSpeaking(): void {
    if (this.activeAudio) {
      this.activeAudio.pause()
      this.activeAudio = null
    }
    this.audioQueue = []
    this.isPlayingAudio = false
  }

  private _setState(state: VoiceState): void {
    if (this.state === state) return
    this.state = state
    this.callbacks.onStateChange(state)
  }

  getState(): VoiceState {
    return this.state
  }

  destroy(): void {
    cancelAnimationFrame(this.levelTimer)
    this.recognition?.stop()
    this.micStream?.getTracks().forEach(t => t.stop())
    this.audioCtx?.close()
  }
}
