// Network helpers: LAN IP, self-signed SSL cert, QR-code startup banner.

import { networkInterfaces } from 'node:os'
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import selfsigned from 'selfsigned'
import qrcode from 'qrcode-terminal'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = join(__dirname, '..')

export function getLanIp() {
  const ifaces = networkInterfaces()
  // Prefer common LAN interfaces first
  const order = ['Wi-Fi', 'Ethernet', 'en0', 'en1', 'wlan0', 'eth0']
  for (const name of order) {
    const list = ifaces[name]
    if (!list) continue
    for (const i of list) {
      if (i.family === 'IPv4' && !i.internal) return i.address
    }
  }
  // Fallback: first non-internal IPv4
  for (const name of Object.keys(ifaces)) {
    for (const i of ifaces[name] || []) {
      if (i.family === 'IPv4' && !i.internal) return i.address
    }
  }
  return '127.0.0.1'
}

export function ensureSslCert() {
  const certPath = join(REPO_ROOT, 'cert.pem')
  const keyPath = join(REPO_ROOT, 'key.pem')
  if (existsSync(certPath) && existsSync(keyPath)) {
    return {
      cert: readFileSync(certPath, 'utf-8'),
      key: readFileSync(keyPath, 'utf-8'),
    }
  }

  const lanIp = getLanIp()
  const attrs = [{ name: 'commonName', value: 'JARVIS Local' }]
  const altNames = [
    { type: 2, value: 'localhost' },     // DNS
    { type: 7, ip: '127.0.0.1' },        // IP
  ]
  if (lanIp !== '127.0.0.1') altNames.push({ type: 7, ip: lanIp })

  const pems = selfsigned.generate(attrs, {
    keySize: 2048,
    days: 365 * 5,
    algorithm: 'sha256',
    extensions: [
      { name: 'basicConstraints', cA: true },
      { name: 'subjectAltName', altNames },
    ],
  })

  writeFileSync(certPath, pems.cert)
  writeFileSync(keyPath, pems.private)
  console.log(`[SSL] Self-signed cert generated for localhost + ${lanIp}`)
  return { cert: pems.cert, key: pems.private }
}

export function printBanner({ port, https }) {
  const lanIp = getLanIp()
  const proto = https ? 'https' : 'http'
  const local = `${proto}://localhost:${port}`
  const lan = `${proto}://${lanIp}:${port}`

  console.log('')
  console.log('='.repeat(64))
  console.log('  J.A.R.V.I.S — ready')
  console.log('='.repeat(64))
  console.log(`  Desktop (this PC):  ${local}`)
  console.log(`  Phone / LAN:        ${lan}`)
  console.log('')

  if (!https) {
    console.log('  WARNING: HTTPS disabled — iPhone microphone access requires HTTPS.')
    console.log('')
  } else {
    console.log('  iPhone note: Safari will warn about the self-signed cert.')
    console.log("              Tap 'Show Details' → 'Visit Website' to continue.")
    console.log('')
  }

  console.log('  Scan this QR code with your phone (same WiFi):')
  console.log('')
  qrcode.generate(lan, { small: true })
  console.log('='.repeat(64))
  console.log('')
}
