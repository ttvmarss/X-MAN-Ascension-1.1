/**
 * Voice module: Web Speech API recognition + Fish Audio TTS playback.
 * Works in Chrome on Windows 10.
 */

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking'

export interface VoiceCallbacks {
  onTranscript: (text: string, final: boolean) => void
  onStateChange: (state: VoiceState) => void
  onAudioLevel: (level: number) => void
}

export class VoiceManager {
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

  constructor(callbacks: VoiceCallbacks) {
    this.callbacks = callbacks
  }

  async init(): Promise<void> {
    await this._initAudioContext()
    this._initSpeechRecognition()
  }

  private async _initAudioContext(): Promise<void> {
    this.audioCtx = new AudioContext()
    try {
      this.micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      const source = this.audioCtx.createMediaStreamSource(this.micStream)
      this.analyser = this.audioCtx.createAnalyser()
      this.analyser.fftSize = 256
      source.connect(this.analyser)
      this._startLevelPolling()
    } catch (e) {
      console.warn('Microphone not accessible:', e)
    }
  }

  private _startLevelPolling(): void {
    const data = new Uint8Array(this.analyser!.frequencyBinCount)
    const tick = () => {
      this.levelTimer = requestAnimationFrame(tick)
      if (!this.analyser) return
      this.analyser.getByteFrequencyData(data)
      const sum = data.reduce((a, b) => a + b, 0)
      const avg = sum / data.length / 255
      this.callbacks.onAudioLevel(avg)
    }
    tick()
  }

  private _initSpeechRecognition(): void {
    const SR = window.SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SR) {
      console.error('Web Speech API not supported. Use Google Chrome.')
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
        const result = event.results[i]
        if (result.isFinal) {
          finalText += result[0].transcript
        } else {
          interim += result[0].transcript
        }
      }
      if (interim) {
        this.callbacks.onTranscript(interim, false)
      }
      if (finalText.trim()) {
        this.callbacks.onTranscript(finalText.trim(), true)
      }
    }

    this.recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error === 'no-speech' || event.error === 'aborted') return
      console.warn('Speech recognition error:', event.error)
    }

    this.recognition.onend = () => {
      // Auto-restart unless we're speaking
      if (this.state !== 'speaking' && this.state !== 'idle') {
        setTimeout(() => this.recognition?.start(), 300)
      }
    }
  }

  startListening(): void {
    if (!this.recognition) return
    this._setState('listening')
    try {
      this.recognition.start()
    } catch (e) {
      // Already started
    }
  }

  stopListening(): void {
    if (!this.recognition) return
    try {
      this.recognition.stop()
    } catch (e) {}
  }

  setProcessing(): void {
    this._setState('processing')
    this.stopListening()
  }

  async playAudioBuffer(buffer: ArrayBuffer): Promise<void> {
    this.audioQueue.push(buffer)
    if (!this.isPlayingAudio) {
      await this._drainQueue()
    }
  }

  private async _drainQueue(): Promise<void> {
    while (this.audioQueue.length > 0) {
      const buf = this.audioQueue.shift()!
      await this._playOnce(buf)
    }
    // Resume listening after speaking
    this._setState('listening')
    this.startListening()
  }

  private _playOnce(buffer: ArrayBuffer): Promise<void> {
    return new Promise((resolve) => {
      this.isPlayingAudio = true
      this._setState('speaking')

      const blob = new Blob([buffer], { type: 'audio/mpeg' })
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      this.activeAudio = audio

      audio.onended = () => {
        URL.revokeObjectURL(url)
        this.isPlayingAudio = false
        this.activeAudio = null
        resolve()
      }

      audio.onerror = () => {
        URL.revokeObjectURL(url)
        this.isPlayingAudio = false
        this.activeAudio = null
        resolve()
      }

      audio.play().catch(() => resolve())
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
