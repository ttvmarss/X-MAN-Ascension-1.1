// FREE JARVIS voice via Microsoft Edge's neural text-to-speech.
// No API key required. Streams audio over WebSocket to MS Edge's public TTS endpoint.
// Voice quality is comparable to paid services (Fish Audio, ElevenLabs).

import { MsEdgeTTS, OUTPUT_FORMAT } from 'msedge-tts'

// Best JARVIS-like voices (British male, deep, authoritative)
const VOICE_OPTIONS = {
  jarvis: 'en-GB-RyanNeural',       // recommended — British, calm, intelligent
  butler: 'en-GB-ThomasNeural',     // alternative British male
  american: 'en-US-GuyNeural',      // American male
  female: 'en-GB-SoniaNeural',      // British female
  narrator: 'en-US-TonyNeural',     // American male, deeper
}

const VOICE_NAME = process.env.JARVIS_VOICE || VOICE_OPTIONS.jarvis
const VOICE_RATE = process.env.JARVIS_RATE || '+0%'     // -50% to +100%
const VOICE_PITCH = process.env.JARVIS_PITCH || '-5%'   // -50% to +50%

let _tts = null
let _initFailed = false

async function getTts() {
  if (_initFailed) return null
  if (_tts) return _tts
  try {
    _tts = new MsEdgeTTS()
    await _tts.setMetadata(VOICE_NAME, OUTPUT_FORMAT.AUDIO_24KHZ_48KBITRATE_MONO_MP3)
    console.log(`[TTS] Microsoft Edge voice ready: ${VOICE_NAME}`)
    return _tts
  } catch (e) {
    console.warn(`[TTS] Edge TTS init failed: ${e.message}. Using browser TTS fallback.`)
    _initFailed = true
    return null
  }
}

/**
 * Synthesize text to MP3 audio.
 * Returns Buffer of MP3 bytes, or null on failure (client should use browser TTS).
 */
export async function textToSpeech(text) {
  if (!text || !text.trim()) return null
  const tts = await getTts()
  if (!tts) return null

  const cleaned = sanitize(text)
  if (!cleaned) return null

  try {
    const result = await tts.toArrayBuffer(cleaned, VOICE_RATE, VOICE_PITCH)
    return Buffer.from(result)
  } catch (e) {
    console.warn(`[TTS] Synthesis failed: ${e.message}`)
    // Try one re-init on transient errors (MS Edge websocket sometimes drops)
    _tts = null
    try {
      const retry = await getTts()
      if (!retry) return null
      const result = await retry.toArrayBuffer(cleaned, VOICE_RATE, VOICE_PITCH)
      return Buffer.from(result)
    } catch (e2) {
      console.warn(`[TTS] Retry failed: ${e2.message}`)
      return null
    }
  }
}

function sanitize(text) {
  return text
    .replace(/```[\s\S]*?```/g, ' code block ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/#{1,6}\s/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

export const VOICES = VOICE_OPTIONS
