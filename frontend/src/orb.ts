/**
 * Three.js audio-reactive particle orb — the MCU JARVIS visual.
 */
import * as THREE from 'three'

export type OrbState = 'idle' | 'listening' | 'thinking' | 'speaking'

const STATE_COLORS: Record<OrbState, THREE.Color> = {
  idle: new THREE.Color(0x00d4ff),
  listening: new THREE.Color(0x0088ff),
  thinking: new THREE.Color(0xffd700),
  speaking: new THREE.Color(0x00ff88),
}

const PARTICLE_COUNT = 3000

export class JarvisOrb {
  private scene: THREE.Scene
  private camera: THREE.PerspectiveCamera
  private renderer: THREE.WebGLRenderer
  private particles!: THREE.Points
  private geometry!: THREE.BufferGeometry
  private basePositions!: Float32Array
  private clock: THREE.Clock
  private state: OrbState = 'idle'
  private audioLevel: number = 0
  private targetColor: THREE.Color
  private currentColor: THREE.Color
  private animId: number = 0

  constructor(canvas: HTMLCanvasElement) {
    this.clock = new THREE.Clock()
    this.targetColor = STATE_COLORS.idle.clone()
    this.currentColor = STATE_COLORS.idle.clone()

    this.scene = new THREE.Scene()
    this.scene.fog = new THREE.FogExp2(0x020d18, 0.15)

    this.camera = new THREE.PerspectiveCamera(60, canvas.clientWidth / canvas.clientHeight, 0.1, 100)
    this.camera.position.z = 3

    this.renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true })
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    this.renderer.setSize(canvas.clientWidth, canvas.clientHeight)
    this.renderer.setClearColor(0x000000, 0)

    this._buildParticles()
    this._addLights()
    this._bindResize(canvas)
    this._animate()
  }

  private _buildParticles() {
    this.geometry = new THREE.BufferGeometry()
    const positions = new Float32Array(PARTICLE_COUNT * 3)
    const colors = new Float32Array(PARTICLE_COUNT * 3)
    const sizes = new Float32Array(PARTICLE_COUNT)
    const randomness = new Float32Array(PARTICLE_COUNT * 3)
    const basePos = new Float32Array(PARTICLE_COUNT * 3)

    const phi_golden = Math.PI * (3 - Math.sqrt(5))

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      // Fibonacci sphere distribution
      const y = 1 - (i / (PARTICLE_COUNT - 1)) * 2
      const radius = Math.sqrt(1 - y * y)
      const theta = phi_golden * i

      const r = 0.8 + Math.random() * 0.3
      const x = Math.cos(theta) * radius * r
      const z = Math.sin(theta) * radius * r
      const yy = y * r

      positions[i * 3] = x
      positions[i * 3 + 1] = yy
      positions[i * 3 + 2] = z

      basePos[i * 3] = x
      basePos[i * 3 + 1] = yy
      basePos[i * 3 + 2] = z

      randomness[i * 3] = (Math.random() - 0.5) * 0.02
      randomness[i * 3 + 1] = (Math.random() - 0.5) * 0.02
      randomness[i * 3 + 2] = (Math.random() - 0.5) * 0.02

      colors[i * 3] = 0
      colors[i * 3 + 1] = 0.83
      colors[i * 3 + 2] = 1

      sizes[i] = Math.random() * 2 + 1
    }

    this.basePositions = basePos
    this.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    this.geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    this.geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))
    this.geometry.setAttribute('randomness', new THREE.BufferAttribute(randomness, 3))

    const material = new THREE.PointsMaterial({
      size: 0.012,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      sizeAttenuation: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })

    this.particles = new THREE.Points(this.geometry, material)
    this.scene.add(this.particles)
  }

  private _addLights() {
    const ambient = new THREE.AmbientLight(0x00d4ff, 0.3)
    this.scene.add(ambient)
    const point = new THREE.PointLight(0x00d4ff, 2, 5)
    point.position.set(2, 2, 2)
    this.scene.add(point)
  }

  private _bindResize(canvas: HTMLCanvasElement) {
    const ro = new ResizeObserver(() => {
      const w = canvas.clientWidth
      const h = canvas.clientHeight
      this.camera.aspect = w / h
      this.camera.updateProjectionMatrix()
      this.renderer.setSize(w, h)
    })
    ro.observe(canvas)
  }

  private _animate() {
    const tick = () => {
      this.animId = requestAnimationFrame(tick)
      const t = this.clock.getElapsedTime()
      const dt = this.clock.getDelta()

      // Lerp color
      this.currentColor.lerp(this.targetColor, 0.05)

      // Update particle positions
      const pos = this.geometry.attributes.position as THREE.BufferAttribute
      const col = this.geometry.attributes.color as THREE.BufferAttribute
      const rnd = this.geometry.attributes.randomness as THREE.BufferAttribute
      const base = this.basePositions

      const scale = 1 + this.audioLevel * 0.4
      const noise = this.audioLevel * 0.15

      for (let i = 0; i < PARTICLE_COUNT; i++) {
        const bx = base[i * 3]
        const by = base[i * 3 + 1]
        const bz = base[i * 3 + 2]

        const rx = rnd.getX(i)
        const ry = rnd.getY(i)
        const rz = rnd.getZ(i)

        const wave = Math.sin(t * 1.5 + bx * 3 + by * 3) * 0.05
        const breathe = Math.sin(t * 0.7) * 0.03

        pos.setXYZ(
          i,
          bx * scale + rx * noise + wave,
          by * scale + ry * noise + breathe,
          bz * scale + rz * noise,
        )

        col.setXYZ(i, this.currentColor.r, this.currentColor.g, this.currentColor.b)
      }

      pos.needsUpdate = true
      col.needsUpdate = true

      // Slow rotation
      this.particles.rotation.y = t * 0.08
      this.particles.rotation.x = Math.sin(t * 0.05) * 0.1

      // Decay audio level
      this.audioLevel *= 0.95

      this.renderer.render(this.scene, this.camera)
    }
    tick()
  }

  setState(state: OrbState) {
    this.state = state
    this.targetColor = STATE_COLORS[state].clone()
  }

  setAudioLevel(level: number) {
    this.audioLevel = Math.max(this.audioLevel, Math.min(level, 1))
  }

  destroy() {
    cancelAnimationFrame(this.animId)
    this.renderer.dispose()
    this.geometry.dispose()
  }
}
