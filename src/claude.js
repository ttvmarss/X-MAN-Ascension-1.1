// Anthropic Claude integration with tool-use dispatch loop.

import Anthropic from '@anthropic-ai/sdk'
import { JARVIS_TOOLS } from './tools.js'
import {
  saveMemory,
  searchMemories,
  addTask,
  getPendingTasks,
} from './memory.js'
import { openBrowser, openApp, spawnBuild, saveNote } from './actions.js'

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

const MODEL_FAST = process.env.CLAUDE_MODEL || 'claude-haiku-4-5-20251001'
const MAX_ITERATIONS = 3

/**
 * Run a Claude conversation turn with tool use.
 *   convo: Conversation instance (will be mutated)
 *   userText: the new user message text
 *   onAction: optional callback(actionName, info) for tool side effects
 * Returns the final assistant text to speak.
 */
export async function turn(convo, userText, onAction = () => {}) {
  convo.addUser(userText)

  let finalText = ''
  let iteration = 0

  while (iteration < MAX_ITERATIONS) {
    iteration++

    const response = await client.messages.create({
      model: MODEL_FAST,
      max_tokens: 600,
      system: convo.systemPrompt(),
      tools: JARVIS_TOOLS,
      messages: convo.getMessages(),
    })

    convo.addAssistantBlocks(response.content)

    const textBlocks = response.content.filter((b) => b.type === 'text')
    const toolUses = response.content.filter((b) => b.type === 'tool_use')

    if (textBlocks.length > 0) {
      finalText = textBlocks.map((b) => b.text).join(' ').trim()
    }

    if (response.stop_reason !== 'tool_use' || toolUses.length === 0) {
      break
    }

    // Execute each tool, collect results, feed back to Claude
    const results = []
    for (const tu of toolUses) {
      const { name, id, input } = tu
      let result
      try {
        result = await dispatchTool(name, input, onAction)
      } catch (e) {
        result = `Tool error: ${e.message}`
      }
      results.push({
        type: 'tool_result',
        tool_use_id: id,
        content: result || 'Done.',
      })
    }
    convo.addToolResults(results)
  }

  return finalText || 'Done, sir.'
}

async function dispatchTool(name, input, onAction) {
  switch (name) {
    case 'remember': {
      saveMemory(input.fact, input.category || 'general', 7)
      onAction('remember', { fact: input.fact })
      return `Saved: "${input.fact.slice(0, 80)}"`
    }
    case 'recall': {
      const hits = searchMemories(input.query, 5)
      if (hits.length === 0) return 'No matching memories found.'
      return hits.map((h) => `- ${h.content}`).join('\n')
    }
    case 'add_task': {
      const id = addTask(input.title, input.priority || 3, input.due_in_hours)
      onAction('task_added', { id, title: input.title })
      return `Task #${id} added: "${input.title}"`
    }
    case 'list_tasks': {
      const tasks = getPendingTasks()
      if (tasks.length === 0) return 'No pending tasks.'
      return tasks
        .slice(0, 10)
        .map((t) => `#${t.id} [P${t.priority}] ${t.title}`)
        .join('\n')
    }
    case 'browse_web': {
      openBrowser(input.query_or_url)
      onAction('browse', { target: input.query_or_url })
      return `Opened browser: ${input.query_or_url}`
    }
    case 'open_app': {
      openApp(input.app)
      onAction('open_app', { app: input.app })
      return `Launched: ${input.app}`
    }
    case 'build_project': {
      const taskId = spawnBuild(input.description, input.project_name)
      onAction('build_started', { task_id: taskId, description: input.description })
      return `Build #${taskId} started. I'll update you when complete.`
    }
    case 'save_note': {
      const path = saveNote(input.content, input.title)
      onAction('note_saved', { path })
      return `Note saved.`
    }
    case 'get_time': {
      return new Date().toLocaleString('en-GB', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    }
    default:
      return `Unknown tool: ${name}`
  }
}
