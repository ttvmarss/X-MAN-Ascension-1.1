/**
 * Jarvis Orb — canvas animation with four visual states.
 * States: idle | listening | processing | speaking
 */

const STATES = {
  IDLE: "idle",
  LISTENING: "listening",
  PROCESSING: "processing",
  SPEAKING: "speaking",
};

/** Golden-angle Fibonacci sphere distribution */
function fibonacciSphere(count, radius) {
  const points = [];
  const golden = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < count; i++) {
    const y = 1 - (i / (count - 1)) * 2;
    const r = Math.sqrt(1 - y * y);
    const theta = golden * i;
    points.push({
      x: Math.cos(theta) * r * radius,
      y: y * radius,
      z: Math.sin(theta) * r * radius,
    });
  }
  return points;
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

class OrbRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.state = STATES.IDLE;
    this.time = 0;
    this.speakPulse = 0;
    this.corePoints = fibonacciSphere(120, 1);
    this.dust = Array.from({ length: 48 }, () => this._spawnDust());
    this._resize();
    window.addEventListener("resize", () => this._resize());
  }

  _spawnDust() {
    const angle = Math.random() * Math.PI * 2;
    const dist = 0.55 + Math.random() * 0.35;
    return {
      angle,
      dist,
      speed: 0.08 + Math.random() * 0.2,
      size: 0.4 + Math.random() * 1.2,
      phase: Math.random() * Math.PI * 2,
    };
  }

  _resize() {
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    this.canvas.width = Math.floor(rect.width * dpr);
    this.canvas.height = Math.floor(rect.height * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.cx = rect.width / 2;
    this.cy = rect.height / 2;
    this.baseRadius = Math.min(rect.width, rect.height) * 0.22;
  }

  setState(state) {
    if (Object.values(STATES).includes(state)) {
      this.state = state;
    }
  }

  /** Called while TTS is active — amplitude 0..1 drives speaking pulse */
  setSpeakAmplitude(amp) {
    this.speakPulse = Math.max(0, Math.min(1, amp));
  }

  _stateParams() {
    switch (this.state) {
      case STATES.LISTENING:
        return {
          breathe: 0.04,
          breatheSpeed: 2.2,
          coreRot: 0.018,
          membraneExpand: 1.06,
          glow: 1.35,
          shimmer: 0.3,
          dustSpeed: 1.4,
        };
      case STATES.PROCESSING:
        return {
          breathe: 0.03,
          breatheSpeed: 3.5,
          coreRot: 0.035,
          membraneExpand: 1.02,
          glow: 1.5,
          shimmer: 0.85,
          dustSpeed: 2.0,
        };
      case STATES.SPEAKING:
        return {
          breathe: 0.07 + this.speakPulse * 0.08,
          breatheSpeed: 5 + this.speakPulse * 4,
          coreRot: 0.022,
          membraneExpand: 1.08 + this.speakPulse * 0.05,
          glow: 1.7 + this.speakPulse * 0.5,
          shimmer: 0.5 + this.speakPulse * 0.6,
          dustSpeed: 1.2 + this.speakPulse,
        };
      default:
        return {
          breathe: 0.025,
          breatheSpeed: 1.1,
          coreRot: 0.006,
          membraneExpand: 1.0,
          glow: 1.0,
          shimmer: 0.1,
          dustSpeed: 0.6,
        };
    }
  }

  /** Organic membrane edge radius at angle theta */
  _membraneRadius(theta, layer, t, params) {
    const wobble =
      Math.sin(theta * 3 + t * 0.7 + layer) * 0.04 +
      Math.sin(theta * 5 - t * 0.5 + layer * 2) * 0.025 +
      Math.sin(theta * 7 + t * 1.1) * 0.015 +
      Math.sin(theta * 11 - t * 0.9 + layer * 0.5) * 0.01;
    const breathe = 1 + Math.sin(t * params.breatheSpeed) * params.breathe;
    const base = (layer === 0 ? 1.0 : 0.97) * params.membraneExpand * breathe;
    return this.baseRadius * base * (1 + wobble);
  }

  _drawMembrane(t, params, layer) {
    const segments = 128;
    const ctx = this.ctx;
    const shimmer = params.shimmer * (0.5 + 0.5 * Math.sin(t * 4 + layer));

    ctx.beginPath();
    for (let i = 0; i <= segments; i++) {
      const theta = (i / segments) * Math.PI * 2;
      const r = this._membraneRadius(theta, layer, t, params);
      const x = this.cx + Math.cos(theta) * r;
      const y = this.cy + Math.sin(theta) * r;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();

    const alpha = layer === 0 ? 0.55 : 0.35;
    ctx.strokeStyle = `rgba(60, 230, 220, ${alpha * params.glow + shimmer * 0.15})`;
    ctx.lineWidth = layer === 0 ? 1.8 : 1.2;
    ctx.shadowColor = "rgba(0, 220, 210, 0.6)";
    ctx.shadowBlur = 12 * params.glow;
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  _drawInnerRing(t, params) {
    const ctx = this.ctx;
    const r = this.baseRadius * 0.72 * (1 + Math.sin(t * params.breatheSpeed) * params.breathe * 0.5);
    ctx.beginPath();
    ctx.arc(this.cx, this.cy, r, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(80, 200, 210, ${0.22 * params.glow})`;
    ctx.lineWidth = 0.8;
    ctx.stroke();
  }

  _drawCore(t, params) {
    const ctx = this.ctx;
    const rotY = t * params.coreRot * 60;
    const rotX = t * params.coreRot * 25;
    const coreR = this.baseRadius * 0.38 * (1 + Math.sin(t * params.breatheSpeed) * params.breathe * 0.3);

    const cosY = Math.cos(rotY);
    const sinY = Math.sin(rotY);
    const cosX = Math.cos(rotX);
    const sinX = Math.sin(rotX);

    const projected = this.corePoints.map((p) => {
      let x = p.x * coreR;
      let y = p.y * coreR;
      let z = p.z * coreR;

      const x1 = x * cosY + z * sinY;
      const z1 = -x * sinY + z * cosY;
      const y2 = y * cosX - z1 * sinX;
      const z2 = y * sinX + z1 * cosX;

      const perspective = 300 / (300 + z2);
      return {
        sx: this.cx + x1 * perspective,
        sy: this.cy + y2 * perspective,
        depth: z2,
      };
    });

    projected.sort((a, b) => a.depth - b.depth);

    for (const pt of projected) {
      const depthNorm = (pt.depth + coreR) / (2 * coreR);
      const size = 1.2 + depthNorm * 1.8;
      const alpha = 0.35 + depthNorm * 0.55;
      ctx.beginPath();
      ctx.arc(pt.sx, pt.sy, size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(120, 255, 245, ${alpha * params.glow})`;
      ctx.fill();
    }
  }

  _drawDust(t, params) {
    const ctx = this.ctx;
    for (const d of this.dust) {
      d.angle += d.speed * 0.004 * params.dustSpeed;
      const wobble = Math.sin(t * 0.8 + d.phase) * 0.04;
      const r = this.baseRadius * (d.dist + wobble);
      const x = this.cx + Math.cos(d.angle) * r;
      const y = this.cy + Math.sin(d.angle) * r;
      const flicker = 0.3 + 0.7 * (0.5 + 0.5 * Math.sin(t * 2 + d.phase));
      ctx.beginPath();
      ctx.arc(x, y, d.size * 0.5, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(90, 220, 215, ${0.15 * flicker * params.glow})`;
      ctx.fill();
    }
  }

  _drawAmbientGlow(t, params) {
    const ctx = this.ctx;
    const r = this.baseRadius * 1.4 * (1 + Math.sin(t * params.breatheSpeed) * params.breathe * 0.2);
    const grad = ctx.createRadialGradient(this.cx, this.cy, 0, this.cx, this.cy, r);
    grad.addColorStop(0, `rgba(20, 80, 90, ${0.12 * params.glow})`);
    grad.addColorStop(0.5, `rgba(10, 40, 50, ${0.06 * params.glow})`);
    grad.addColorStop(1, "rgba(5, 5, 8, 0)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
  }

  tick(dt) {
    this.time += dt;
    const t = this.time;
    const params = this._stateParams();
    const ctx = this.ctx;

    ctx.clearRect(0, 0, this.canvas.width / (window.devicePixelRatio || 1), this.canvas.height / (window.devicePixelRatio || 1));

    this._drawAmbientGlow(t, params);
    this._drawDust(t, params);
    this._drawMembrane(t, params, 0);
    this._drawMembrane(t, params, 1);
    this._drawInnerRing(t, params);
    this._drawCore(t, params);
  }

  start() {
    let last = performance.now();
    const loop = (now) => {
      const dt = Math.min((now - last) / 1000, 0.05);
      last = now;
      this.tick(dt);
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
}

window.OrbRenderer = OrbRenderer;
window.ORB_STATES = STATES;
