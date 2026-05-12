// Three-tier conversation memory: rolling buffer + per-session compression + long-term store.

import { saveSummary, getRecentSummaries } from './memory.js'

const MAX_BUFFER = 20
const KEEP_AFTER_COMPRESS = 10

export class Conversation {
  constructor(userName = 'sir') {
    this.userName = userName
    this.buffer = []
    this.rollingSummary = ''

    const past = getRecentSummaries(2)
    if (past.length > 0) {
      this.rollingSummary = 'From previous sessions: ' + past.join(' | ')
    }
  }

  addUser(text) {
    this.buffer.push({ role: 'user', content: text })
    this._maybeCompress()
  }

  addAssistantBlocks(blocks) {
    // Anthropic-style content blocks (text + tool_use)
    this.buffer.push({ role: 'assistant', content: blocks })
  }

  addToolResults(results) {
    this.buffer.push({ role: 'user', content: results })
  }

  getMessages() {
    return [...this.buffer]
  }

  systemPrompt(extraContext = '') {
    const parts = [
      `You are JARVIS — Just A Rather Very Intelligent System. ` +
        `You are a witty, competent AI assistant running on Windows 10. ` +
        `Address the user as "${this.userName}". ` +
        `Be concise, dry, and British in tone. ` +
        `Voice responses should be 1-3 sentences unless detail is requested. ` +
        `Never break character. Use the tools available when actions are needed.`,
    ]
    if (this.rollingSummary) parts.push(this.rollingSummary)
    if (extraContext) parts.push(extraContext)
    return parts.join('\n\n')
  }

  _maybeCompress() {
    if (this.buffer.length < MAX_BUFFER) return
    const old = this.buffer.slice(0, MAX_BUFFER - KEEP_AFTER_COMPRESS)
    this.buffer = this.buffer.slice(MAX_BUFFER - KEEP_AFTER_COMPRESS)
    const lines = old
      .map((m) => {
        const text =
          typeof m.content === 'string'
            ? m.content
            : (m.content || [])
                .filter((b) => b.type === 'text')
                .map((b) => b.text)
                .join(' ')
        return `${m.role.toUpperCase()}: ${text}`
      })
      .slice(0, 8)
    const summary = 'Earlier in session: ' + lines.join(' | ')
    this.rollingSummary = this.rollingSummary
      ? this.rollingSummary + ' || ' + summary
      : summary
  }

  end() {
    if (this.buffer.length === 0) return
    const lines = this.buffer.slice(-6).map((m) => {
      const text =
        typeof m.content === 'string'
          ? m.content
          : (m.content || [])
              .filter((b) => b.type === 'text')
              .map((b) => b.text)
              .join(' ')
      return `${m.role}: ${text}`
    })
    const stamp = new Date().toISOString().slice(0, 10)
    saveSummary(`Session ${stamp}: ` + lines.join(' | '))
  }
}
