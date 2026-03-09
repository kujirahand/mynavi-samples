import init, { AquariumSim } from "./pkg/env_fish.js";

const TAU = Math.PI * 2;

const DEFAULT_CONFIG = {
  fishCount: 10,
  schoolFishCount: 28,
  environmentSound: {
    enabled: true,
    volume: 0.045,
  },
  speed: {
    main: 1.0,
    school: 1.0,
    round: 1.0,
    shark: 1.55,
    ray: 0.8,
  },
  visual: {
    plantMotion: 1.6,
    bubbleDensity: 1.8,
    lifeGame: {
      enabled: true,
      density: 0.23,
      stepSeconds: 0.9,
      spawnEverySteps: 5,
      opacity: 0.36,
      cellSize: 14,
    },
  },
};

const FISH_VARIANTS = {
  "round-a": { body: "./assets/fish-a.svg", tail: "./assets/fish-tail-a.svg", kind: "round", role: 0 },
  "round-b": { body: "./assets/fish-b.svg", tail: "./assets/fish-tail-b.svg", kind: "round", role: 0 },
  "round-c": { body: "./assets/fish-c.svg", tail: "./assets/fish-tail-c.svg", kind: "round", role: 0 },
  "round-d": { body: "./assets/fish-d.svg", tail: "./assets/fish-tail-d.svg", kind: "round", role: 0 },
  "round-e": { body: "./assets/fish-e.svg", tail: "./assets/fish-tail-e.svg", kind: "round", role: 0 },
  "round-f": { body: "./assets/fish-f.svg", tail: "./assets/fish-tail-f.svg", kind: "round", role: 0 },
  shark: { body: "./assets/fish-shark.svg", tail: "./assets/fish-tail-shark.svg", kind: "shark", role: 1 },
  ray: { body: "./assets/fish-ray.svg", tail: "./assets/fish-tail-ray.svg", kind: "ray", role: 2 },
};

const ROUND_VARIANTS = ["round-a", "round-b", "round-c", "round-d", "round-e", "round-f"];

const aquarium = document.getElementById("aquarium");
const fishLayer = document.getElementById("fish-layer");
const schoolLayer = document.getElementById("school-layer");
const backCanvas = document.getElementById("back-particles");
const frontCanvas = document.getElementById("front-particles");
const plantLayer = document.getElementById("plant-layer");
const lifeCanvas = document.getElementById("life-layer");

const state = {
  config: DEFAULT_CONFIG,
  sim: null,
  fishes: [],
  school: [],
  schoolCenter: { x: 0, y: 0, vx: 0, vy: 0 },
  backParticles: [],
  bubbles: [],
  life: {
    enabled: false,
    cols: 0,
    rows: 0,
    cell: 14,
    timer: 0,
    stepSeconds: 0.9,
    spawnEverySteps: 5,
    stepCount: 0,
    opacity: 0.36,
    density: 0.23,
    grid: new Uint8Array(0),
    next: new Uint8Array(0),
    glow: new Float32Array(0),
  },
  lastTime: performance.now(),
  audio: null,
};

class WaterSound {
  constructor(volume) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    this.ctx = new Ctx();
    this.volume = Math.max(0, Math.min(volume, 0.12));

    const length = this.ctx.sampleRate * 2;
    const buffer = this.ctx.createBuffer(1, length, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < length; i += 1) data[i] = Math.random() * 2 - 1;

    this.source = this.ctx.createBufferSource();
    this.source.buffer = buffer;
    this.source.loop = true;

    this.lowpass = this.ctx.createBiquadFilter();
    this.lowpass.type = "lowpass";
    this.lowpass.frequency.value = 720;
    this.lowpass.Q.value = 0.7;

    this.highpass = this.ctx.createBiquadFilter();
    this.highpass.type = "highpass";
    this.highpass.frequency.value = 70;

    this.gain = this.ctx.createGain();
    this.gain.gain.value = 0;

    this.lfo = this.ctx.createOscillator();
    this.lfo.frequency.value = 0.09;
    this.lfoGain = this.ctx.createGain();
    this.lfoGain.gain.value = this.volume * 0.22;

    this.source.connect(this.lowpass);
    this.lowpass.connect(this.highpass);
    this.highpass.connect(this.gain);
    this.gain.connect(this.ctx.destination);

    this.lfo.connect(this.lfoGain);
    this.lfoGain.connect(this.gain.gain);

    this.source.start();
    this.lfo.start();
  }

  async start() {
    if (this.ctx.state === "suspended") await this.ctx.resume();
    const t = this.ctx.currentTime;
    this.gain.gain.cancelScheduledValues(t);
    this.gain.gain.linearRampToValueAtTime(this.volume, t + 1.4);
  }
}

function clampNumber(value, min, max, fallback) {
  if (typeof value !== "number" || Number.isNaN(value)) return fallback;
  return Math.min(max, Math.max(min, value));
}

async function loadConfig() {
  try {
    const res = await fetch("./config.json", { cache: "no-store" });
    if (!res.ok) return DEFAULT_CONFIG;
    const json = await res.json();
    return {
      fishCount: clampNumber(json.fishCount, 3, 28, DEFAULT_CONFIG.fishCount),
      schoolFishCount: clampNumber(json.schoolFishCount, 0, 60, DEFAULT_CONFIG.schoolFishCount),
      environmentSound: {
        enabled: Boolean(json.environmentSound?.enabled ?? DEFAULT_CONFIG.environmentSound.enabled),
        volume: clampNumber(json.environmentSound?.volume, 0, 0.12, DEFAULT_CONFIG.environmentSound.volume),
      },
      speed: {
        main: clampNumber(json.speed?.main, 0.4, 2.5, DEFAULT_CONFIG.speed.main),
        school: clampNumber(json.speed?.school, 0.3, 3, DEFAULT_CONFIG.speed.school),
        round: clampNumber(json.speed?.round, 0.4, 2.6, DEFAULT_CONFIG.speed.round),
        shark: clampNumber(json.speed?.shark, 0.6, 3.2, DEFAULT_CONFIG.speed.shark),
        ray: clampNumber(json.speed?.ray, 0.4, 2.4, DEFAULT_CONFIG.speed.ray),
      },
      visual: {
        plantMotion: clampNumber(json.visual?.plantMotion, 0.5, 3, DEFAULT_CONFIG.visual.plantMotion),
        bubbleDensity: clampNumber(json.visual?.bubbleDensity, 0.5, 4, DEFAULT_CONFIG.visual.bubbleDensity),
        lifeGame: {
          enabled: Boolean(json.visual?.lifeGame?.enabled ?? DEFAULT_CONFIG.visual.lifeGame.enabled),
          density: clampNumber(json.visual?.lifeGame?.density, 0.05, 0.6, DEFAULT_CONFIG.visual.lifeGame.density),
          stepSeconds: clampNumber(json.visual?.lifeGame?.stepSeconds, 0.35, 2.2, DEFAULT_CONFIG.visual.lifeGame.stepSeconds),
          spawnEverySteps: clampNumber(
            json.visual?.lifeGame?.spawnEverySteps,
            1,
            40,
            DEFAULT_CONFIG.visual.lifeGame.spawnEverySteps
          ),
          opacity: clampNumber(json.visual?.lifeGame?.opacity, 0.08, 0.7, DEFAULT_CONFIG.visual.lifeGame.opacity),
          cellSize: clampNumber(json.visual?.lifeGame?.cellSize, 8, 24, DEFAULT_CONFIG.visual.lifeGame.cellSize),
        },
      },
    };
  } catch {
    return DEFAULT_CONFIG;
  }
}

function buildMainLayout(count) {
  const layout = [];
  for (let i = 0; i < count; i += 1) {
    layout.push(ROUND_VARIANTS[i % ROUND_VARIANTS.length]);
  }
  if (count >= 4) {
    layout[1] = "shark";
    layout[Math.floor(count * 0.58)] = "ray";
  }
  return layout;
}

function resizeCanvases() {
  const rect = aquarium.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  for (const canvas of [lifeCanvas, backCanvas, frontCanvas]) {
    canvas.width = Math.floor(rect.width * dpr);
    canvas.height = Math.floor(rect.height * dpr);
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
}

function seedLifeGame() {
  const settings = state.config.visual.lifeGame;
  const rect = aquarium.getBoundingClientRect();
  const cell = settings.cellSize;
  const cols = Math.max(22, Math.floor(rect.width / cell));
  const rows = Math.max(14, Math.floor(rect.height / cell));
  const size = cols * rows;

  state.life.enabled = settings.enabled;
  state.life.cols = cols;
  state.life.rows = rows;
  state.life.cell = cell;
  state.life.timer = 0;
  state.life.stepCount = 0;
  state.life.stepSeconds = settings.stepSeconds;
  state.life.spawnEverySteps = settings.spawnEverySteps;
  state.life.opacity = settings.opacity;
  state.life.density = settings.density;
  state.life.grid = new Uint8Array(size);
  state.life.next = new Uint8Array(size);
  state.life.glow = new Float32Array(size);
  lifeCanvas.style.opacity = `${settings.enabled ? settings.opacity : 0}`;

  if (!settings.enabled) return;

  for (let y = 0; y < rows; y += 1) {
    for (let x = 0; x < cols; x += 1) {
      const idx = y * cols + x;
      const wave = (Math.sin(x * 0.36) + Math.cos(y * 0.29)) * 0.08;
      const alive = Math.random() < settings.density + wave;
      state.life.grid[idx] = alive ? 1 : 0;
      state.life.glow[idx] = alive ? 0.5 + Math.random() * 0.4 : 0;
    }
  }
}

function stepLifeGame() {
  const life = state.life;
  if (!life.enabled) return;

  const { cols, rows, grid, next, glow } = life;
  let aliveCount = 0;
  life.stepCount = (life.stepCount || 0) + 1;

  for (let y = 0; y < rows; y += 1) {
    const ym = (y + rows - 1) % rows;
    const yp = (y + 1) % rows;
    for (let x = 0; x < cols; x += 1) {
      const xm = (x + cols - 1) % cols;
      const xp = (x + 1) % cols;
      const idx = y * cols + x;

      const n =
        grid[ym * cols + xm] +
        grid[ym * cols + x] +
        grid[ym * cols + xp] +
        grid[y * cols + xm] +
        grid[y * cols + xp] +
        grid[yp * cols + xm] +
        grid[yp * cols + x] +
        grid[yp * cols + xp];

      const alive = grid[idx] === 1;
      const nextAlive = alive ? n === 2 || n === 3 : n === 3;
      next[idx] = nextAlive ? 1 : 0;
      aliveCount += next[idx];

      if (nextAlive) {
        glow[idx] = Math.min(1, glow[idx] + 0.25);
      } else {
        glow[idx] *= 0.86;
      }
    }
  }

  const periodicSpawn = life.stepCount % life.spawnEverySteps === 0;
  if (aliveCount < cols || periodicSpawn) {
    const spawnCount = periodicSpawn ? Math.floor(cols * 1.8) : cols * 2;
    const spawnProb = periodicSpawn ? life.density * 0.85 : life.density * 0.65;
    for (let i = 0; i < spawnCount; i += 1) {
      const idx = Math.floor(Math.random() * grid.length);
      next[idx] = Math.random() < spawnProb ? 1 : next[idx];
    }
  }

  life.grid = next;
  life.next = grid;
}

function updateAndDrawLife(dt) {
  const ctx = lifeCanvas.getContext("2d");
  const rect = aquarium.getBoundingClientRect();
  ctx.clearRect(0, 0, rect.width, rect.height);

  const life = state.life;
  if (!life.enabled) return;

  life.timer += dt;
  while (life.timer >= life.stepSeconds) {
    life.timer -= life.stepSeconds;
    stepLifeGame();
  }

  const { cols, rows, cell, grid, glow } = life;
  for (let y = 0; y < rows; y += 1) {
    for (let x = 0; x < cols; x += 1) {
      const idx = y * cols + x;
      const g = glow[idx];
      if (g < 0.035) continue;
      const alpha = (grid[idx] ? 0.24 : 0.11) * g;
      ctx.fillStyle = `rgba(120, 188, 255, ${alpha})`;
      const cx = x * cell + cell * 0.5;
      const cy = y * cell + cell * 0.5;
      const radius = cell * (grid[idx] ? 0.33 : 0.24);
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, TAU);
      ctx.fill();
    }
  }
}

function createFishElements(layout) {
  fishLayer.innerHTML = "";
  state.fishes = [];

  for (let i = 0; i < layout.length; i += 1) {
    const config = FISH_VARIANTS[layout[i]];
    const fish = document.createElement("div");
    fish.className = `fish fish--${config.kind}`;

    const tail = document.createElement("img");
    tail.className = "fish-tail";
    tail.alt = "";
    tail.src = config.tail;
    tail.setAttribute("aria-hidden", "true");

    const body = document.createElement("img");
    body.className = "fish-body";
    body.alt = "魚";
    body.src = config.body;

    fish.appendChild(tail);
    fish.appendChild(body);
    fishLayer.appendChild(fish);

    const kindSpeed =
      config.kind === "shark"
        ? state.config.speed.shark
        : config.kind === "ray"
          ? state.config.speed.ray
          : state.config.speed.round;

    state.fishes.push({
      el: fish,
      body,
      tail,
      role: config.role,
      kind: config.kind,
      speedFactor: kindSpeed,
      phase: Math.random() * TAU,
      swimRate: config.kind === "shark" ? 2.1 : config.kind === "ray" ? 0.9 : 1.2 + Math.random() * 0.85,
      flex: config.kind === "ray" ? 0.35 + Math.random() * 0.25 : 0.5 + Math.random() * 0.5,
      tint: (Math.random() - 0.5) * 14,
      sat: 0.95 + Math.random() * 0.2,
      bright: 0.93 + Math.random() * 0.18,
    });
  }
}

function createSchoolFish() {
  schoolLayer.innerHTML = "";
  state.school = [];

  for (let i = 0; i < state.config.schoolFishCount; i += 1) {
    const node = document.createElement("img");
    node.className = "school-fish";
    node.src = "./assets/fish-minnow.svg";
    node.alt = "";
    node.setAttribute("aria-hidden", "true");
    schoolLayer.appendChild(node);

    state.school.push({
      el: node,
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      phase: Math.random() * TAU,
      orbit: 26 + Math.random() * 84,
      speed: (0.55 + Math.random() * 0.9) * state.config.speed.school,
      bob: 2 + Math.random() * 4,
      scale: 0.72 + Math.random() * 0.58,
    });
  }
}

function resetSchoolCenter() {
  const rect = aquarium.getBoundingClientRect();
  state.schoolCenter.x = rect.width * 0.38;
  state.schoolCenter.y = rect.height * 0.56;
  state.schoolCenter.vx = 0;
  state.schoolCenter.vy = 0;

  for (const m of state.school) {
    m.x = state.schoolCenter.x + (Math.random() - 0.5) * 120;
    m.y = state.schoolCenter.y + (Math.random() - 0.5) * 70;
  }
}

function updateSchool(dt, t) {
  const rect = aquarium.getBoundingClientRect();
  const c = state.schoolCenter;

  const targetX = rect.width * (0.35 + Math.sin(t * 0.08) * 0.2);
  const targetY = rect.height * (0.55 + Math.sin(t * 0.11 + 0.8) * 0.13);

  c.vx += (targetX - c.x) * dt * 0.38;
  c.vy += (targetY - c.y) * dt * 0.38;
  c.vx *= 0.985;
  c.vy *= 0.985;
  c.x += c.vx;
  c.y += c.vy;

  for (let i = 0; i < state.school.length; i += 1) {
    const m = state.school[i];
    const angle = t * m.speed + m.phase + i * 0.18;
    const tx = c.x + Math.cos(angle) * m.orbit;
    const ty = c.y + Math.sin(angle * 1.15) * (m.orbit * 0.36);

    m.vx += (tx - m.x) * dt * 3.2;
    m.vy += (ty - m.y) * dt * 3.2;
    m.vx *= 0.93;
    m.vy *= 0.93;

    m.x += m.vx;
    m.y += m.vy;

    if (m.x < -20) m.x = rect.width + 20;
    if (m.x > rect.width + 20) m.x = -20;
    if (m.y < -20) m.y = rect.height + 20;
    if (m.y > rect.height + 20) m.y = -20;

    const dir = m.vx >= 0 ? 1 : -1;
    const wag = Math.sin(t * 8 + m.phase) * 6;
    const bob = Math.sin(t * 1.8 + m.phase) * m.bob;

    m.el.style.opacity = `${0.5 + m.scale * 0.35}`;
    m.el.style.transform = `translate(${m.x - 10}px, ${m.y + bob - 5}px) rotate(${wag * 0.12}deg) scale(${dir * m.scale}, ${m.scale})`;
  }
}

function seedParticles() {
  const rect = aquarium.getBoundingClientRect();
  const density = state.config.visual.bubbleDensity;

  state.backParticles = Array.from({ length: Math.floor(180 * density) }, () => ({
    x: Math.random() * rect.width,
    y: Math.random() * rect.height,
    size: Math.random() * 2.4 + 0.6,
    drift: (Math.random() - 0.5) * 9,
    rise: Math.random() * 9 + 4,
    alpha: Math.random() * 0.22 + 0.05,
  }));

  state.bubbles = Array.from({ length: Math.floor(52 * density) }, () => ({
    x: Math.random() * rect.width,
    y: Math.random() * rect.height,
    r: Math.random() * 6 + 2,
    rise: Math.random() * 34 + 18,
    sway: Math.random() * TAU,
    alpha: Math.random() * 0.3 + 0.14,
  }));
}

function drawParticles(dt, t) {
  const rect = aquarium.getBoundingClientRect();
  const backCtx = backCanvas.getContext("2d");
  const frontCtx = frontCanvas.getContext("2d");

  backCtx.clearRect(0, 0, rect.width, rect.height);
  for (const p of state.backParticles) {
    p.y -= p.rise * dt * 0.35;
    p.x += Math.sin(t * 0.12 + p.y * 0.03) * dt * p.drift;
    if (p.y < -8) {
      p.y = rect.height + 8;
      p.x = Math.random() * rect.width;
    }
    if (p.x < -10) p.x = rect.width + 10;
    if (p.x > rect.width + 10) p.x = -10;

    backCtx.beginPath();
    backCtx.fillStyle = `rgba(201, 238, 248, ${p.alpha})`;
    backCtx.arc(p.x, p.y, p.size, 0, TAU);
    backCtx.fill();
  }

  frontCtx.clearRect(0, 0, rect.width, rect.height);
  for (const b of state.bubbles) {
    b.y -= b.rise * dt;
    b.x += Math.sin(t * 0.9 + b.sway) * dt * 12;
    if (b.y < -12) {
      b.y = rect.height + 12;
      b.x = Math.random() * rect.width;
      b.r = Math.random() * 6 + 2;
    }

    frontCtx.beginPath();
    frontCtx.strokeStyle = `rgba(220, 245, 255, ${b.alpha})`;
    frontCtx.lineWidth = 1.25;
    frontCtx.arc(b.x, b.y, b.r, 0, TAU);
    frontCtx.stroke();
  }
}

function updateMainFish(dt, t) {
  const rect = aquarium.getBoundingClientRect();
  state.sim.step(dt * state.config.speed.main, rect.width, rect.height);
  const snapshot = state.sim.snapshot();

  for (let i = 0; i < state.fishes.length; i += 1) {
    const idx = i * 5;
    const x = snapshot[idx + 0];
    const y = snapshot[idx + 1];
    const dir = snapshot[idx + 2];
    const scale = snapshot[idx + 3];
    const depth = snapshot[idx + 4];

    const fish = state.fishes[i];
    const wag = Math.sin(t * fish.swimRate * 6 + fish.phase);
    const bodyYaw = fish.kind === "ray" ? Math.sin(t * 3.1 + fish.phase) * 2.6 : wag * fish.flex * 3.1;
    const tailAngle = fish.kind === "ray" ? Math.sin(t * 2.6 + fish.phase) * 10 : wag * fish.flex * 19;
    const tailStretch = fish.kind === "ray" ? 1 + Math.sin(t * 3 + fish.phase) * 0.05 : 1 + Math.abs(wag) * 0.16;
    const bob = Math.sin(t * 0.9 + i * 1.7) * (1.6 + depth * 1.2);

    fish.el.style.opacity = `${0.55 + depth * 0.45}`;
    fish.el.style.zIndex = `${2 + Math.floor(depth * 10)}`;
    fish.el.style.transform = `translate(${x - 56}px, ${y + bob - 30}px) scale(${dir * scale}, ${scale})`;
    fish.body.style.transform = `translateY(${wag * 0.8}px) rotate(${bodyYaw}deg)`;
    fish.body.style.filter = `hue-rotate(${fish.tint}deg) saturate(${fish.sat}) brightness(${fish.bright})`;
    fish.tail.style.transform = `rotate(${tailAngle}deg) scaleY(${tailStretch})`;
    fish.tail.style.filter = `hue-rotate(${fish.tint * 0.85}deg) saturate(${fish.sat * 0.98}) brightness(${fish.bright * 0.95})`;
  }
}

function animate(now) {
  const dt = Math.min((now - state.lastTime) / 1000, 0.033);
  const t = now / 1000;
  state.lastTime = now;

  plantLayer.style.transform = `translateX(${Math.sin(t * 0.42) * 2.2}px)`;
  updateAndDrawLife(dt);
  updateMainFish(dt, t);
  updateSchool(dt, t);
  drawParticles(dt, t);
  requestAnimationFrame(animate);
}

function setupConfiguredAudio() {
  const settings = state.config.environmentSound;
  if (!settings.enabled) return;

  state.audio = new WaterSound(settings.volume);
  const starter = async () => {
    await state.audio.start();
    window.removeEventListener("pointerdown", starter);
    window.removeEventListener("keydown", starter);
    window.removeEventListener("touchstart", starter);
  };

  window.addEventListener("pointerdown", starter, { once: true });
  window.addEventListener("keydown", starter, { once: true });
  window.addEventListener("touchstart", starter, { once: true });
}

async function boot() {
  state.config = await loadConfig();
  document.documentElement.style.setProperty("--plant-motion", `${state.config.visual.plantMotion}`);

  await init();

  const layout = buildMainLayout(state.config.fishCount);
  const rect = aquarium.getBoundingClientRect();

  state.sim = new AquariumSim(rect.width, rect.height, layout.length, Date.now() >>> 0);
  createFishElements(layout);
  createSchoolFish();
  resetSchoolCenter();

  for (let i = 0; i < state.fishes.length; i += 1) {
    state.sim.set_role(i, state.fishes[i].role);
    if (typeof state.sim.set_speed_factor === "function") {
      state.sim.set_speed_factor(i, state.fishes[i].speedFactor);
    }
  }

  resizeCanvases();
  seedLifeGame();
  seedParticles();
  setupConfiguredAudio();

  window.addEventListener("resize", () => {
    resizeCanvases();
    seedLifeGame();
    seedParticles();
    resetSchoolCenter();
  });

  requestAnimationFrame(animate);
}

boot();
