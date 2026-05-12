/**
 * JARVIS Frontend — Windows 10 + iPhone Edition
 * Dual-mode: continuous voice on desktop, push-to-talk on mobile/iOS.
 */
import { JarvisOrb } from './orb'
import { VoiceManager, detectMode } from './voice'
import type { VoiceState, VoiceMode } from './voice'

// ── URLs (relative to current host so it works on LAN/phone) ─────────────────
const isSecure = window.location.protocol === 'https:'
const WS_PROTOCOL = isSecure ? 'wss' : 'ws'
const HOST = window.location.host
const WS_URL = `${WS_PROTOCOL}://${HOST}/ws`
const TRANSCRIBE_URL = `${window.location.origin}/api/transcribe`

// ── DOM refs ──────────────────────────────────────────────────────────────────
const canvas = document.getElementById('orb-canvas') as HTMLCanvasElement
const transcriptEl = document.getElementById('transcript-text') as HTMLElement
const responseEl = document.getElementById('response-text') as HTMLElement
const stateLabelEl = document.getElementById('state-label') as HTMLElement
const clickOverlay = document.getElementById('click-overlay') as HTMLElement
const clickMessage = document.getElementById('click-message') as HTMLElement
const pttButton = document.getElementById('ptt-button') as HTMLButtonElement
const versionEl = document.getElementById('version') as HTMLElement

// ── State ─────────────────────────────────────────────────────────────────────
let orb: JarvisOrb
let voice: VoiceManager
let ws: WebSocket | null = null
let wsReady = false
let reconnectTimer: number | null = null
let mode: VoiceMode = detectMode()
let pttHolding = false

// ── WebSocket ─────────────────────────────────────────────────────────────────
function connectWS() {
  if (ws) {
    ws.onclose = null
    ws.close()
  }
  ws = new WebSocket(WS_URL)
  ws.binaryType = 'arraybuffer'

  ws.onopen = () => {
    wsReady = true
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  ws.onmessage = async (event: MessageEvent) => {
    if (event.data instanceof ArrayBuffer) {
      orb.setState('speaking')
      await voice.playAudioBuffer(event.data)
    } else {
      try {
        const msg = JSON.parse(event.data as string)
        handleServerMessage(msg)
      } catch (e) {
        console.warn('Bad message:', event.data)
      }
    }
  }

  ws.onclose = () => {
    wsReady = false
    reconnectTimer = window.setTimeout(connectWS, 3000)
  }

  ws.onerror = (e) => console.error('WebSocket error:', e)
}

function sendTranscript(text: string, final: boolean) {
  if (!wsReady || !ws) return
  ws.send(JSON.stringify({ type: 'transcript', text, final }))
}

// ── Server message handler ────────────────────────────────────────────────────
function handleServerMessage(msg: Record<string, unknown>) {
  const type = msg.type as string

  if (type === 'response') {
    setResponse(msg.text as string)
    orb.setState('speaking')
    setUIState('speaking')
  } else if (type === 'thinking') {
    orb.setState('thinking')
    setUIState('thinking')
  } else if (type === 'tts_fallback') {
    browserTTS(msg.text as string)
  } else if (type === 'action') {
    const action = msg.action as string
    const taskId = msg.task_id as string
    showActionNotice(action, taskId)
  }
}

// ── Browser TTS fallback (uses Windows George voice, iOS Daniel) ─────────────
function browserTTS(text: string) {
  if (!('speechSynthesis' in window)) return
  const utt = new SpeechSynthesisUtterance(text)
  utt.lang = 'en-GB'
  utt.rate = 0.95
  utt.pitch = 0.85

  const voices = speechSynthesis.getVoices()
  const british =
    voices.find(v => v.name.toLowerCase().includes('daniel')) ||      // iOS
    voices.find(v => v.name.toLowerCase().includes('george')) ||     // Windows
    voices.find(v => v.lang === 'en-GB') ||
    voices.find(v => v.lang.startsWith('en'))
  if (british) utt.voice = british

  utt.onstart = () => { orb.setState('speaking'); setUIState('speaking') }
  utt.onend = () => {
    if (mode === 'continuous') { orb.setState('listening'); setUIState('listening') }
    else { orb.setState('idle'); setUIState('idle') }
  }
  speechSynthesis.cancel()
  speechSynthesis.speak(utt)
}

// ── Voice callbacks ───────────────────────────────────────────────────────────
function onTranscript(text: string, final: boolean) {
  setTranscript(text, final)
  if (final && text.trim()) {
    setUIState('thinking')
    orb.setState('thinking')
    sendTranscript(text, true)
  }
}

function onVoiceStateChange(state: VoiceState) {
  if (state === 'recording') {
    orb.setState('listening')
    setUIState('recording')
  } else if (state === 'listening') {
    orb.setState('listening')
    setUIState('listening')
  } else if (state === 'speaking') {
    orb.setState('speaking')
    setUIState('speaking')
  } else if (state === 'idle') {
    orb.setState('idle')
    setUIState('idle')
  } else if (state === 'processing') {
    orb.setState('thinking')
    setUIState('thinking')
  }
}

function onAudioLevel(level: number) {
  orb.setAudioLevel(level * 3)
}

// ── UI helpers ────────────────────────────────────────────────────────────────
const STATE_LABELS: Record<string, string> = {
  idle: mode === 'push_to_talk' ? 'HOLD TO TALK' : 'STANDBY',
  listening: 'LISTENING',
  recording: 'RECORDING',
  thinking: 'PROCESSING',
  speaking: 'SPEAKING',
}

function setUIState(state: string) {
  document.body.className = state
  stateLabelEl.textContent = STATE_LABELS[state] || state.toUpperCase()
}

function setTranscript(text: string, final: boolean) {
  transcriptEl.textContent = final ? `"${text}"` : text
}

function setResponse(text: string) {
  responseEl.textContent = text
}

function showActionNotice(action: string, taskId: string) {
  const notices: Record<string, string> = {
    build_started: `Build started (#${taskId})`,
    research_started: `Research in progress (#${taskId})`,
  }
  console.log('[JARVIS]', notices[action] || action)
}

// ── Push-to-talk button (mobile / iOS) ───────────────────────────────────────
function bindPushToTalk() {
  if (mode === 'continuous') {
    pttButton.style.display = 'none'
    return
  }
  pttButton.style.display = 'flex'
  clickMessage.textContent = 'Tap to begin'

  const start = async (e: Event) => {
    e.preventDefault()
    if (pttHolding) return
    pttHolding = true
    pttButton.classList.add('active')
    await voice.startRecording()
  }
  const stop = async (e: Event) => {
    e.preventDefault()
    if (!pttHolding) return
    pttHolding = false
    pttButton.classList.remove('active')
    await voice.stopRecording(TRANSCRIBE_URL)
  }

  // Touch (iOS/Android)
  pttButton.addEventListener('touchstart', start, { passive: false })
  pttButton.addEventListener('touchend', stop, { passive: false })
  pttButton.addEventListener('touchcancel', stop, { passive: false })

  // Mouse (desktop fallback)
  pttButton.addEventListener('mousedown', start)
  pttButton.addEventListener('mouseup', stop)
  pttButton.addEventListener('mouseleave', stop)
}

// ── PWA: register service worker ─────────────────────────────────────────────
async function registerSW() {
  if (!('serviceWorker' in navigator)) return
  try {
    await navigator.serviceWorker.register('/sw.js')
  } catch (e) {
    // Service worker registration failure is non-fatal
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  orb = new JarvisOrb(canvas)
  voice = new VoiceManager({
    onTranscript,
    onStateChange: onVoiceStateChange,
    onAudioLevel,
  }, mode)

  versionEl.textContent = mode === 'continuous' ? 'Desktop' : 'Mobile'

  bindPushToTalk()

  clickOverlay.addEventListener('click', async () => {
    try {
      await voice.init()
    } catch (e) {
      clickMessage.textContent = 'Microphone permission denied'
      return
    }
    clickOverlay.classList.add('hidden')
    connectWS()

    if (mode === 'continuous') {
      voice.startListening()
      orb.setState('listening')
      setUIState('listening')
    } else {
      orb.setState('idle')
      setUIState('idle')
    }
  })

  setInterval(() => {
    if (wsReady && ws) ws.send(JSON.stringify({ type: 'ping' }))
  }, 30000)

  speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices()
  registerSW()
}

init()
