const startScreen = document.getElementById("start-screen");
const appShell = document.getElementById("app-shell");
const titleForm = document.getElementById("title-form");
const titleInput = document.getElementById("title-input");
const sessionTitle = document.getElementById("session-title");
const chat = document.getElementById("chat");
const ideaForm = document.getElementById("idea-form");
const ideaInput = document.getElementById("idea-input");
const sakuraLayer = document.getElementById("sakura-layer");

const idleMs = (window.APP_CONFIG?.idleSeconds || 20) * 1000;
let currentTitle = "";
let lastActivityAt = Date.now();
let suggestInFlight = false;
let isComposing = false;
let ambientEffectStarted = false;

function addMessage(kind, text) {
  const el = document.createElement("article");
  el.className = `msg ${kind}`;
  el.textContent = text;
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
  scatterNatureBurst();
}

function touchActivity() {
  lastActivityAt = Date.now();
}

function scatterNatureBurst() {
  const count = 30;
  for (let i = 0; i < count; i += 1) {
    const chip = document.createElement("span");
    const isLeaf = Math.random() < 0.45;
    chip.className = isLeaf ? "leaf" : "petal";
    chip.style.left = `${Math.random() * 100}vw`;
    chip.style.animationDuration = `${4 + Math.random() * 4}s`;
    chip.style.animationDelay = `${Math.random() * 0.45}s`;
    chip.style.transform = `rotate(${Math.random() * 360}deg)`;
    sakuraLayer.appendChild(chip);
    setTimeout(() => chip.remove(), 8600);
  }
}

function spawnAmbientPetal() {
  const petal = document.createElement("span");
  petal.className = "petal";
  petal.style.left = `${Math.random() * 100}vw`;
  petal.style.animationDuration = `${5 + Math.random() * 5}s`;
  petal.style.animationDelay = "0s";
  petal.style.transform = `rotate(${Math.random() * 360}deg)`;
  sakuraLayer.appendChild(petal);
  setTimeout(() => petal.remove(), 11000);
}

function startAmbientSakura() {
  if (ambientEffectStarted) {
    return;
  }
  ambientEffectStarted = true;
  setInterval(spawnAmbientPetal, 280);
}

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "通信に失敗しました" }));
    throw new Error(err.detail || "エラーが発生しました");
  }
  return res.json();
}

async function sendIdea() {
  const text = ideaInput.value.trim();
  if (!text || !currentTitle) {
    return;
  }

  ideaInput.value = "";
  touchActivity();
  addMessage("user", `あなた: ${text}`);
  ideaInput.disabled = true;

  try {
    const data = await postJSON("/idea", { title: currentTitle, idea: text });
    addMessage("ai", `AI: ${data.message}`);
  } catch (err) {
    addMessage("suggest", `SYSTEM: ${err.message}`);
  } finally {
    ideaInput.disabled = false;
    ideaInput.focus();
  }
}

async function maybeSuggest() {
  if (!currentTitle || suggestInFlight) {
    return;
  }
  const idleFor = Date.now() - lastActivityAt;
  if (idleFor < idleMs) {
    return;
  }

  suggestInFlight = true;
  try {
    const data = await postJSON("/suggest", { title: currentTitle });
    addMessage("suggest", `AIの提案: ${data.message}`);
    touchActivity();
  } catch (err) {
    addMessage("suggest", `SYSTEM: ${err.message}`);
    touchActivity();
  } finally {
    suggestInFlight = false;
  }
}

titleForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = titleInput.value.trim();
  if (!title) {
    return;
  }

  try {
    const data = await postJSON("/start", { title });
    currentTitle = data.title;
    sessionTitle.textContent = `タイトル: ${currentTitle}`;
    startScreen.classList.add("hidden");
    appShell.classList.remove("hidden");
    addMessage("ai", "AI: 準備OKです。どんどんアイデアを投げてください！");
    touchActivity();
    ideaInput.focus();
  } catch (err) {
    alert(err.message);
  }
});

ideaForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await sendIdea();
});

ideaInput.addEventListener("input", touchActivity);
ideaInput.addEventListener("compositionstart", () => {
  isComposing = true;
});
ideaInput.addEventListener("compositionend", () => {
  isComposing = false;
  touchActivity();
});
ideaInput.addEventListener("keydown", async (event) => {
  // 日本語IME変換中のEnter(確定キー)では送信しない
  if (isComposing || event.isComposing || event.keyCode === 229) {
    return;
  }

  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    await sendIdea();
  }
});

setInterval(maybeSuggest, 1000);
startAmbientSakura();
