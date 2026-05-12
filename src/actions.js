// Windows actions: launch apps, open URLs, spawn Claude Code builds, save notes.
// All cross-platform-safe but optimized for Windows.

import { spawn, exec } from 'node:child_process'
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { homedir, platform } from 'node:os'
import { randomBytes } from 'node:crypto'

const IS_WIN = platform() === 'win32'
const NOTES_DIR = join(homedir(), 'Documents', 'JARVIS Notes')
const PROJECTS_DIR = join(homedir(), 'Documents', 'JARVIS Projects')
const CLAUDE_CODE = process.env.CLAUDE_CODE_PATH || 'claude'

mkdirSync(NOTES_DIR, { recursive: true })
mkdirSync(PROJECTS_DIR, { recursive: true })

const _builds = new Map()

export function openUrl(url) {
  if (IS_WIN) {
    spawn('cmd', ['/c', 'start', '""', url], { detached: true, stdio: 'ignore' }).unref()
  } else if (platform() === 'darwin') {
    spawn('open', [url], { detached: true, stdio: 'ignore' }).unref()
  } else {
    spawn('xdg-open', [url], { detached: true, stdio: 'ignore' }).unref()
  }
  return true
}

export function openBrowser(queryOrUrl) {
  const url = /^https?:\/\//.test(queryOrUrl)
    ? queryOrUrl
    : `https://www.google.com/search?q=${encodeURIComponent(queryOrUrl)}`
  return openUrl(url)
}

export function openApp(appName) {
  if (IS_WIN) {
    spawn('cmd', ['/c', 'start', '""', appName], { detached: true, stdio: 'ignore' }).unref()
  } else {
    spawn(appName, [], { detached: true, stdio: 'ignore' }).unref()
  }
  return true
}

export function saveNote(content, title = '') {
  const now = new Date()
  const stamp = now.toISOString().replace(/[:.]/g, '-').slice(0, 19)
  if (!title) {
    const firstLine = (content.split('\n')[0] || '').slice(0, 50).trim()
    title = firstLine || `Note ${stamp}`
  }
  const safe = title.replace(/[^a-z0-9 _-]/gi, '_').slice(0, 60)
  const filename = `${stamp}_${safe}.txt`
  const path = join(NOTES_DIR, filename)
  const body = `# ${title}\nCreated: ${now.toLocaleString()}\n\n${content}\n`
  writeFileSync(path, body, 'utf-8')
  return path
}

export function spawnBuild(description, projectName) {
  const taskId = randomBytes(4).toString('hex')
  if (!projectName) {
    const words = description.toLowerCase().split(/\s+/).slice(0, 3)
    projectName = words.filter((w) => /^[a-z]+$/.test(w)).join('-') || 'jarvis-project'
  }
  const projectDir = join(PROJECTS_DIR, `${projectName}-${taskId}`)
  mkdirSync(projectDir, { recursive: true })

  const proc = spawn(CLAUDE_CODE, ['--print', description], {
    cwd: projectDir,
    shell: IS_WIN,
    detached: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  const build = {
    id: taskId,
    description,
    project_dir: projectDir,
    status: 'running',
    started_at: Date.now(),
    output: '',
  }
  _builds.set(taskId, build)

  proc.stdout?.on('data', (chunk) => {
    build.output += chunk.toString()
  })
  proc.stderr?.on('data', (chunk) => {
    build.output += chunk.toString()
  })
  proc.on('exit', (code) => {
    build.status = code === 0 ? 'done' : 'failed'
    build.completed_at = Date.now()
  })
  proc.on('error', (err) => {
    build.status = 'failed'
    build.output += `\n[error] ${err.message}`
  })
  proc.unref()
  return taskId
}

export function getBuild(taskId) {
  return _builds.get(taskId)
}

export function listBuilds() {
  return [..._builds.values()]
}
