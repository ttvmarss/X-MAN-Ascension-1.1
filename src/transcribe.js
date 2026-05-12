// Optional server-side speech-to-text for iOS Safari fallback.
// Tries `nodejs-whisper` (whisper.cpp bindings). If not installed,
// returns null and the client uses webkitSpeechRecognition instead.

import { writeFileSync, unlinkSync, mkdirSync } from 'node:fs'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { randomBytes } from 'node:crypto'

let _whisperLoader = null

async function getWhisper() {
  if (_whisperLoader) return _whisperLoader
  _whisperLoader = (async () => {
    try {
      const mod = await import('nodejs-whisper')
      console.log('[STT] nodejs-whisper loaded.')
      return mod
    } catch {
      console.log('[STT] nodejs-whisper not installed. iOS will use browser STT.')
      return null
    }
  })()
  return _whisperLoader
}

export async function transcribeAudio(audioBuffer, contentType = 'audio/webm') {
  if (!audioBuffer || audioBuffer.length === 0) return null
  const whisper = await getWhisper()
  if (!whisper) return null

  const ext = contentType.includes('mp4') || contentType.includes('m4a')
    ? '.m4a'
    : contentType.includes('ogg') ? '.ogg'
    : contentType.includes('wav') ? '.wav'
    : '.webm'

  const tmpDir = join(tmpdir(), 'jarvis-stt')
  mkdirSync(tmpDir, { recursive: true })
  const tmpFile = join(tmpDir, `${Date.now()}-${randomBytes(4).toString('hex')}${ext}`)
  writeFileSync(tmpFile, audioBuffer)

  try {
    const fn = whisper.nodewhisper || whisper.default
    const result = await fn(tmpFile, {
      modelName: process.env.WHISPER_MODEL || 'base.en',
      autoDownloadModelName: process.env.WHISPER_MODEL || 'base.en',
      removeWavFileAfterTranscription: false,
      withCuda: false,
      whisperOptions: {
        outputInText: true,
        language: 'en',
      },
    })
    const text = typeof result === 'string' ? result : (result?.text || '')
    return text.trim() || null
  } catch (e) {
    console.warn('[STT] Whisper failed:', e.message)
    return null
  } finally {
    try { unlinkSync(tmpFile) } catch {}
  }
}
