/**
 * JARVIS Frontend — Windows 10 Edition
 * State machine: connects WebSocket, drives orb + voice + UI.
 */
import { JarvisOrb } from './orb'
import { VoiceManager } from './voice'
import type { VoiceState } from './voice'

// ── Config ────────────────────────────────────────────────────────────────────
const WS_HOST = window.location.hostname || 'localhost'
// Backend runs on 8000 (separate from Vite dev server on 8340)
// When built and served by the backend directly, use same host/port
const WS_PORT = import.meta.env.VITE_WS_PORT ? Number(import.meta.env.VITE_WS_PORT) : 8000
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss' : 'ws'
const WS_URL = `${WS_PROTOCOL}://${WS_HOST}:${WS_PORT}/ws`

// ── DOM refs ──────────────────────────────────────────────────────────────────
const canvas = document.getElementById('orb-canvas') as HTMLCanvasElement
const transcriptEl = document.getElementById('transcript-text') as HTMLElement
const responseEl = document.getElementById('response-text') as HTMLElement
const stateLabelEl = document.getElementById('state-label') as HTMLElement
const clickOverlay = document.getElementById('click-overlay') as HTMLElement

// ── State ─────────────────────────────────────────────────────────────────────
let orb: JarvisOrb
let voice: VoiceManager
let ws: WebSocket | null = null
let wsReady = false
let reconnectTimer: number | null = null
let pendingTranscript = ''

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
    console.log('[JARVIS] WebSocket connected')
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  ws.onmessage = async (event: MessageEvent) => {
    if (event.data instanceof ArrayBuffer) {
      // Binary = TTS audio
      orb.setState('speaking')
      await voice.playAudioBuffer(event.data)
    } else {
      const msg = JSON.parse(event.data as string)
      handleServerMessage(msg)
    }
  }

  ws.onclose = () => {
    wsReady = false
    console.warn('[JARVIS] WebSocket closed — reconnecting in 3s')
    reconnectTimer = window.setTimeout(connectWS, 3000)
  }

  ws.onerror = (e) => {
    console.error('[JARVIS] WebSocket error:', e)
  }
}

function sendTranscript(text: string, final: boolean) {
  if (!wsReady || !ws) return
  ws.send(JSON.stringify({ type: 'transcript', text, final }))
}

// ── Server message handler ────────────────────────────────────────────────────
function handleServerMessage(msg: Record<string, unknown>) {
  const type = msg.type as string

  if (type === 'response') {
    const text = msg.text as string
    setResponse(text)
    orb.setState('speaking')
    setUIState('speaking')
  } else if (type === 'thinking') {
    orb.setState('thinking')
    setUIState('thinking')
    setTranscript(pendingTranscript, true)
  } else if (type === 'tts_fallback') {
    // No audio — use browser TTS as fallback
    const text = msg.text as string
    browserTTS(text)
  } else if (type === 'action') {
    const action = msg.action as string
    const taskId = msg.task_id as string
    showActionNotice(action, taskId)
  } else if (type === 'pong') {
    // heartbeat ack
  }
}

// ── Browser TTS fallback (Windows has built-in voices) ───────────────────────
function browserTTS(text: string) {
  if (!('speechSynthesis' in window)) return
  const utt = new SpeechSynthesisUtterance(text)
  utt.lang = 'en-GB'
  utt.rate = 0.95
  utt.pitch = 0.85

  // Prefer a British voice if available
  const voices = speechSynthesis.getVoices()
  const british = voices.find(v => v.lang.startsWith('en-GB') && v.name.toLowerCase().includes('george'))
    || voices.find(v => v.lang.startsWith('en-GB'))
    || voices.find(v => v.lang.startsWith('en'))

  if (british) utt.voice = british

  utt.onstart = () => { orb.setState('speaking'); setUIState('speaking') }
  utt.onend = () => { orb.setState('listening'); setUIState('listening') }

  speechSynthesis.speak(utt)
}

// ── Voice callbacks ───────────────────────────────────────────────────────────
function onTranscript(text: string, final: boolean) {
  setTranscript(text, final)
  pendingTranscript = text

  if (final && text.trim()) {
    setUIState('thinking')
    orb.setState('thinking')
    sendTranscript(text, true)
  }
}

function onVoiceStateChange(state: VoiceState) {
  if (state === 'listening') {
    orb.setState('listening')
    setUIState('listening')
  } else if (state === 'speaking') {
    orb.setState('speaking')
    setUIState('speaking')
  }
}

function onAudioLevel(level: number) {
  orb.setAudioLevel(level * 3)
}

// ── UI helpers ────────────────────────────────────────────────────────────────
const STATE_LABELS: Record<string, string> = {
  idle: 'STANDBY',
  listening: 'LISTENING',
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
    build_started: `Build started (ID: ${taskId}). I'll notify you when complete.`,
    research_started: `Research in progress (ID: ${taskId}).`,
  }
  const msg = notices[action] || `Action: ${action}`
  console.log('[JARVIS]', msg)
}

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  orb = new JarvisOrb(canvas)

  voice = new VoiceManager({
    onTranscript,
    onStateChange: onVoiceStateChange,
    onAudioLevel,
  })

  // Click overlay to unlock audio context (required by browsers)
  clickOverlay.addEventListener('click', async () => {
    clickOverlay.classList.add('hidden')
    await voice.init()
    connectWS()
    voice.startListening()
    orb.setState('listening')
    setUIState('listening')
  })

  // Ping heartbeat
  setInterval(() => {
    if (wsReady && ws) {
      ws.send(JSON.stringify({ type: 'ping' }))
    }
  }, 30000)

  // Load voices list (needed for TTS fallback selection)
  speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices()
}

init()
