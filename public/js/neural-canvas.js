/**
 * SLH Neural Canvas — Living System Layer
 * A persistent, low-cost background canvas that turns every page into a
 * living organism: neurons (human=warm, digital=cool) + DNA helix +
 * synaptic connections that pulse with system activity.
 *
 * Mounts itself once. Respects prefers-reduced-motion.
 * Pauses when tab is hidden. Pauses when CPU is throttled.
 *
 * Public API:
 *   NeuralCanvas.start()     — idempotent, called by shared.js
 *   NeuralCanvas.stop()      — pause + remove
 *   NeuralCanvas.pulse(kind) — fire a synaptic flash
 *                              kind: 'human' | 'digital' | 'token'
 *   NeuralCanvas.setDensity(0..1) — scale node count at runtime
 */
(function (global) {
  'use strict';

  const STATE = {
    canvas: null,
    ctx: null,
    nodes: [],
    pulses: [],
    raf: null,
    lastTs: 0,
    running: false,
    width: 0,
    height: 0,
    dpr: 1,
    density: 1,
    helixPhase: 0,
    reducedMotion: false
  };

  const COLORS = {
    human:    { r: 255, g: 154, b: 60  },  // warm orange — humans
    digital:  { r: 94,  g: 214, b: 255 },  // cyan — digital nodes
    token:    { r: 255, g: 209, b: 102 },  // gold — tokens
    purple:   { r: 177, g: 139, b: 255 },  // neural glow
    dna_a:    { r: 94,  g: 214, b: 255 },  // strand A
    dna_b:    { r: 177, g: 139, b: 255 }   // strand B
  };

  function rand(min, max) { return Math.random() * (max - min) + min; }
  function pick(arr)      { return arr[Math.floor(Math.random() * arr.length)]; }

  function createNodes() {
    const baseCount = Math.round((STATE.width * STATE.height) / 28000);
    const count = Math.max(18, Math.min(80, Math.round(baseCount * STATE.density)));
    STATE.nodes = [];
    for (let i = 0; i < count; i++) {
      const kind = Math.random() < 0.35 ? 'human' : (Math.random() < 0.85 ? 'digital' : 'token');
      STATE.nodes.push({
        x: rand(0, STATE.width),
        y: rand(0, STATE.height),
        vx: rand(-0.12, 0.12),
        vy: rand(-0.12, 0.12),
        r: rand(1.2, 2.8),
        kind: kind,
        phase: rand(0, Math.PI * 2),
        speed: rand(0.6, 1.6)
      });
    }
  }

  function resize() {
    if (!STATE.canvas) return;
    STATE.dpr = Math.min(window.devicePixelRatio || 1, 2);
    STATE.width = window.innerWidth;
    STATE.height = window.innerHeight;
    STATE.canvas.width = STATE.width * STATE.dpr;
    STATE.canvas.height = STATE.height * STATE.dpr;
    STATE.canvas.style.width = STATE.width + 'px';
    STATE.canvas.style.height = STATE.height + 'px';
    STATE.ctx.setTransform(STATE.dpr, 0, 0, STATE.dpr, 0, 0);
    createNodes();
  }

  function drawHelix(ts) {
    const ctx = STATE.ctx;
    const w = STATE.width;
    const h = STATE.height;
    const cx = w * 0.5;
    const amp = Math.min(w, h) * 0.18;
    const segments = 80;
    const len = h + 80;
    const startY = -40;
    STATE.helixPhase += 0.0006 * (ts - STATE.lastTs || 16);

    ctx.lineWidth = 1.2;

    // strand A
    ctx.beginPath();
    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const y = startY + t * len;
      const x = cx + Math.sin(t * Math.PI * 4 + STATE.helixPhase) * amp;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    const ga = ctx.createLinearGradient(0, 0, 0, h);
    ga.addColorStop(0, 'rgba(94,214,255,0.0)');
    ga.addColorStop(0.5, 'rgba(94,214,255,0.20)');
    ga.addColorStop(1, 'rgba(94,214,255,0.0)');
    ctx.strokeStyle = ga;
    ctx.stroke();

    // strand B (offset by PI)
    ctx.beginPath();
    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const y = startY + t * len;
      const x = cx + Math.sin(t * Math.PI * 4 + STATE.helixPhase + Math.PI) * amp;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    const gb = ctx.createLinearGradient(0, 0, 0, h);
    gb.addColorStop(0, 'rgba(177,139,255,0.0)');
    gb.addColorStop(0.5, 'rgba(177,139,255,0.20)');
    gb.addColorStop(1, 'rgba(177,139,255,0.0)');
    ctx.strokeStyle = gb;
    ctx.stroke();

    // rungs every N segments
    ctx.strokeStyle = 'rgba(255,209,102,0.10)';
    ctx.lineWidth = 0.8;
    for (let i = 0; i <= segments; i += 4) {
      const t = i / segments;
      const y = startY + t * len;
      const xa = cx + Math.sin(t * Math.PI * 4 + STATE.helixPhase) * amp;
      const xb = cx + Math.sin(t * Math.PI * 4 + STATE.helixPhase + Math.PI) * amp;
      ctx.beginPath();
      ctx.moveTo(xa, y);
      ctx.lineTo(xb, y);
      ctx.stroke();
    }
  }

  function drawSynapses() {
    const ctx = STATE.ctx;
    const nodes = STATE.nodes;
    const maxDist = Math.min(STATE.width, STATE.height) * 0.16;
    ctx.lineWidth = 0.6;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d > maxDist) continue;
        const alpha = (1 - d / maxDist) * 0.18;
        // Cross-kind connections (human↔digital) glow purple — symbiosis
        const cross = a.kind !== b.kind && (a.kind === 'human' || b.kind === 'human');
        const c = cross ? COLORS.purple : COLORS.digital;
        ctx.strokeStyle = `rgba(${c.r},${c.g},${c.b},${alpha})`;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }
  }

  function drawNodes(ts) {
    const ctx = STATE.ctx;
    for (const n of STATE.nodes) {
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < -10) n.x = STATE.width + 10;
      if (n.x > STATE.width + 10) n.x = -10;
      if (n.y < -10) n.y = STATE.height + 10;
      if (n.y > STATE.height + 10) n.y = -10;

      const c = COLORS[n.kind] || COLORS.digital;
      const breath = 0.6 + 0.4 * Math.sin(ts * 0.001 * n.speed + n.phase);
      const radius = n.r * (1 + 0.3 * breath);

      // outer glow
      const grd = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, radius * 6);
      grd.addColorStop(0, `rgba(${c.r},${c.g},${c.b},${0.25 * breath})`);
      grd.addColorStop(1, `rgba(${c.r},${c.g},${c.b},0)`);
      ctx.fillStyle = grd;
      ctx.beginPath();
      ctx.arc(n.x, n.y, radius * 6, 0, Math.PI * 2);
      ctx.fill();

      // core
      ctx.fillStyle = `rgba(${c.r},${c.g},${c.b},${0.85})`;
      ctx.beginPath();
      ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawPulses(ts, dt) {
    const ctx = STATE.ctx;
    const remaining = [];
    for (const p of STATE.pulses) {
      p.life -= dt;
      if (p.life <= 0) continue;
      const t = 1 - (p.life / p.total);
      const r = p.maxR * t;
      const c = COLORS[p.kind] || COLORS.digital;
      ctx.strokeStyle = `rgba(${c.r},${c.g},${c.b},${(1 - t) * 0.6})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
      ctx.stroke();
      remaining.push(p);
    }
    STATE.pulses = remaining;
  }

  function tick(ts) {
    if (!STATE.running) return;
    const dt = STATE.lastTs ? Math.min(ts - STATE.lastTs, 64) : 16;
    STATE.ctx.clearRect(0, 0, STATE.width, STATE.height);
    drawHelix(ts);
    drawSynapses();
    drawNodes(ts);
    drawPulses(ts, dt);
    STATE.lastTs = ts;
    STATE.raf = requestAnimationFrame(tick);
  }

  function start() {
    if (STATE.running) return;
    STATE.reducedMotion = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (STATE.reducedMotion) return; // respect user preference
    if (document.getElementById('slh-neural-canvas')) return;

    const canvas = document.createElement('canvas');
    canvas.id = 'slh-neural-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    canvas.style.cssText = [
      'position:fixed',
      'inset:0',
      'width:100%',
      'height:100%',
      'pointer-events:none',
      'z-index:-1',
      'opacity:0.85'
    ].join(';');
    document.body.appendChild(canvas);

    STATE.canvas = canvas;
    STATE.ctx = canvas.getContext('2d', { alpha: true });
    STATE.running = true;
    resize();
    window.addEventListener('resize', resize, { passive: true });
    document.addEventListener('visibilitychange', onVisibility);
    STATE.raf = requestAnimationFrame(tick);
  }

  function stop() {
    STATE.running = false;
    if (STATE.raf) cancelAnimationFrame(STATE.raf);
    window.removeEventListener('resize', resize);
    document.removeEventListener('visibilitychange', onVisibility);
    if (STATE.canvas && STATE.canvas.parentNode) STATE.canvas.parentNode.removeChild(STATE.canvas);
    STATE.canvas = null;
    STATE.ctx = null;
    STATE.nodes = [];
    STATE.pulses = [];
  }

  function onVisibility() {
    if (document.hidden) {
      if (STATE.raf) cancelAnimationFrame(STATE.raf);
      STATE.running = false;
    } else if (STATE.canvas) {
      STATE.running = true;
      STATE.lastTs = 0;
      STATE.raf = requestAnimationFrame(tick);
    }
  }

  function pulse(kind, x, y) {
    if (!STATE.canvas) return;
    if (typeof x !== 'number') x = STATE.width * 0.5;
    if (typeof y !== 'number') y = STATE.height * 0.5;
    STATE.pulses.push({
      x: x, y: y,
      kind: kind || 'digital',
      life: 1200, total: 1200,
      maxR: Math.min(STATE.width, STATE.height) * 0.25
    });
  }

  function setDensity(d) {
    STATE.density = Math.max(0.2, Math.min(2, d));
    if (STATE.canvas) createNodes();
  }

  global.NeuralCanvas = { start: start, stop: stop, pulse: pulse, setDensity: setDensity };
})(window);
