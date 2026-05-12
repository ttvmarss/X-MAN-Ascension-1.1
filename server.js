// JARVIS — Node.js backend, Windows 10 + iPhone.
// Voice loop: WebSocket transcripts → Claude (tool use) → MS Edge TTS (free) → audio back.

import 'dotenv/config'
import { createServer as createHttpServer } from 'node:http'
import { createServer as createHttpsServer } from 'node:https'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { existsSync, readFileSync } from 'node:fs'

import express from 'express'
import { WebSocketServer } from 'ws'

import { Conversation } from './src/conversation.js'
import { turn } from './src/claude.js'
import { textToSpeech } from './src/tts.js'
import { ensureSslCert, printBanner } from './src/net.js'

const __dirname = dirname(fileURLToPath(import.meta.url))
const FRONTEND_DIST = join(__dirname, 'frontend', 'dist')

const PORT = Number(process.env.PORT || 8000)
const HOST = process.env.HOST || '0.0.0.0'
const USE_HTTPS = (process.env.USE_HTTPS || 'auto').toLowerCase()
const USER_NAME = process.env.USER_NAME || 'sir'

if (!process.env.ANTHROPIC_API_KEY) {
  console.error('[FATAL] ANTHROPIC_API_KEY not set. Edit .env and restart.')
  process.exit(1)
}

// ── HTTP app ──────────────────────────────────────────────────────────────
const app = express()
app.use(express.raw({ type: ['audio/*', 'application/octet-stream'], limit: '20mb' }))
app.use(express.json({ limit: '1mb' }))

if (existsSync(FRONTEND_DIST)) {
  app.use(express.static(FRONTEND_DIST))
} else {
  app.get('/', (_, res) => {
    res.type('text/plain').send(
      'JARVIS backend online. Frontend not built yet.\n' +
        'Run: cd frontend && npm install && npm run build\n' +
        'Then restart.'
    )
  })
}

app.get('/health', (_, res) => {
  res.json({
    status: 'online',
    user: USER_NAME,
    tts: 'msedge-tts (free)',
  })
})

// iOS / Safari fallback: receive audio, transcribe server-side.
// To enable, install optional `nodejs-whisper` package (see CLAUDE.md).
app.post('/api/transcribe', async (req, res) => {
  try {
    const { transcribeAudio } = await import('./src/transcribe.js')
    const text = await transcribeAudio(req.body, req.get('content-type'))
    if (text === null) {
      res.status(503).json({ error: 'transcription unavailable', text: '' })
    } else {
      res.json({ text })
    }
  } catch (e) {
    console.warn('[STT]', e.message)
    res.status(503).json({ error: 'transcription unavailable', text: '' })
  }
})

// ── SSL setup ─────────────────────────────────────────────────────────────
let server
let useHttps = false

if (USE_HTTPS !== 'false') {
  try {
    const { cert, key } = ensureSslCert()
    server = createHttpsServer({ cert, key }, app)
    useHttps = true
  } catch (e) {
    console.warn(`[SSL] Falling back to HTTP: ${e.message}`)
    server = createHttpServer(app)
  }
} else {
  server = createHttpServer(app)
}

// ── WebSocket ─────────────────────────────────────────────────────────────
const wss = new WebSocketServer({ server, path: '/ws' })

wss.on('connection', async (ws, req) => {
  console.log(`[WS] Client connected from ${req.socket.remoteAddress}`)
  const convo = new Conversation(USER_NAME)

  // Initial greeting
  await sendResponse(ws, `Good ${timeOfDay()}, ${USER_NAME}. JARVIS online.`)

  ws.on('message', async (raw) => {
    let msg
    try {
      msg = JSON.parse(raw.toString())
    } catch {
      msg = { type: 'transcript', text: raw.toString(), final: true }
    }

    if (msg.type === 'ping') {
      ws.send(JSON.stringify({ type: 'pong' }))
      return
    }

    if (msg.type === 'end_session') {
      convo.end()
      ws.close()
      return
    }

    if (msg.type !== 'transcript') return
    const text = (msg.text || '').trim()
    if (!text || msg.final === false) return

    ws.send(JSON.stringify({ type: 'thinking' }))

    try {
      const replyText = await turn(convo, text, (action, info) => {
        try {
          ws.send(JSON.stringify({ type: 'action', action, ...info }))
        } catch {}
      })
      await sendResponse(ws, replyText)
    } catch (e) {
      console.error('[TURN]', e)
      await sendResponse(
        ws,
        `My apologies, ${USER_NAME}. Something went sideways. Try again.`
      )
    }
  })

  ws.on('close', () => {
    convo.end()
    console.log('[WS] Client disconnected.')
  })

  ws.on('error', (e) => console.warn('[WS]', e.message))
})

async function sendResponse(ws, text) {
  if (ws.readyState !== ws.OPEN) return
  ws.send(JSON.stringify({ type: 'response', text }))
  const audio = await textToSpeech(text)
  if (audio && ws.readyState === ws.OPEN) {
    ws.send(audio)
  } else if (ws.readyState === ws.OPEN) {
    // Tell client to use browser TTS fallback
    ws.send(JSON.stringify({ type: 'tts_fallback', text }))
  }
}

function timeOfDay() {
  const h = new Date().getHours()
  if (h < 12) return 'morning'
  if (h < 17) return 'afternoon'
  return 'evening'
}

// ── Start ─────────────────────────────────────────────────────────────────
server.listen(PORT, HOST, () => {
  printBanner({ port: PORT, https: useHttps })
})

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n[JARVIS] Shutting down...')
  wss.clients.forEach((c) => c.close())
  server.close(() => process.exit(0))
  setTimeout(() => process.exit(0), 2000)
})
