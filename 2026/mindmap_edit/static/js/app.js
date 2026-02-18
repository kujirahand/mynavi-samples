const statusEl = document.getElementById("status");
const themeInput = document.getElementById("themeInput");
const saveBtn = document.getElementById("saveBtn");
const loadBtn = document.getElementById("loadBtn");
const container = document.getElementById("jsmind_container");

let jm = null;
let expandingNodeIds = new Set();

function isImeComposing(event) {
  return event.isComposing || event.keyCode === 229;
}

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.style.color = isError ? "#b42318" : "#202124";
}

function uid() {
  return `n_${crypto.randomUUID()}`;
}

function createMind(nodes) {
  const mind = {
    meta: { name: "MindEdit", author: "MindEdit", version: "1.0" },
    format: "node_array",
    data: nodes,
  };

  if (jm) {
    jm.show(mind);
    return;
  }

  jm = new jsMind({
    container: "jsmind_container",
    editable: true,
    theme: "primary",
    view: {
      hmargin: 80,
      vmargin: 40,
      line_width: 2,
      line_color: "#8d99ae",
    },
  });
  jm.show(mind);
}

function ensureSelectedNode() {
  const node = jm?.get_selected_node();
  if (!node) {
    setStatus("ノードを選択してください", true);
    return null;
  }
  return node;
}

async function generateFromTheme(theme) {
  setStatus("アイデアを生成中...");
  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ theme }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "生成に失敗しました");
  createMind(data.nodes);
  setStatus("生成完了。Enterで編集、Shift+Enterで追加、ダブルクリックでAI展開");
}

async function expandNode(nodeId, topic) {
  if (expandingNodeIds.has(nodeId)) return;
  expandingNodeIds.add(nodeId);
  setStatus(`"${topic}" を展開中...`);

  try {
    const node = jm.get_node(nodeId);
    const parent = node && node.parent ? node.parent.topic : null;

    const res = await fetch("/api/expand", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, parentTopic: parent }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "展開に失敗しました");

    const existingChildren = new Set((node.children || []).map((c) => c.topic));
    let added = 0;
    for (const idea of data.ideas || []) {
      if (!existingChildren.has(idea)) {
        jm.add_node(nodeId, uid(), idea);
        added += 1;
      }
    }
    setStatus(added ? `${added}件の子ノードを追加しました` : "追加できる新規アイデアがありませんでした");
  } catch (err) {
    setStatus(err.message || "展開処理でエラーが発生しました", true);
  } finally {
    expandingNodeIds.delete(nodeId);
  }
}

function bindHotkeys() {
  document.addEventListener("keydown", (e) => {
    if (isImeComposing(e)) return;
    if (!jm) return;
    if (document.activeElement === themeInput) return;

    if (e.key === "Enter" && e.shiftKey) {
      e.preventDefault();
      const node = ensureSelectedNode();
      if (!node) return;
      const newNode = jm.add_node(node.id, uid(), "新しいノード");
      jm.select_node(newNode.id);
      jm.begin_edit(newNode.id);
      setStatus("子ノードを追加しました");
      return;
    }

    if (e.key === "Enter") {
      e.preventDefault();
      const node = ensureSelectedNode();
      if (!node) return;
      jm.begin_edit(node.id);
      setStatus("ノード編集中...");
    }
  });
}

function bindDoubleClickExpand() {
  container.addEventListener("dblclick", async (e) => {
    const target = e.target.closest("jmnode");
    if (!target || !jm) return;
    const nodeId = target.getAttribute("nodeid");
    if (!nodeId) return;
    const node = jm.get_node(nodeId);
    if (!node) return;
    await expandNode(nodeId, node.topic);
  });
}

async function saveMind() {
  if (!jm) {
    setStatus("保存対象のマインドマップがありません", true);
    return;
  }
  const nodes = jm.get_data("node_array").data;
  const res = await fetch("/api/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nodes }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "保存に失敗しました");
  setStatus(`保存しました (${new Date(data.savedAt).toLocaleString()})`);
}

async function loadMind() {
  const res = await fetch("/api/load");
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "読み込みに失敗しました");
  if (!data.nodes || data.nodes.length === 0) {
    createMind([{ id: "root", isroot: true, topic: "MindEdit" }]);
    setStatus("保存データがないため初期マップを表示");
    return;
  }
  createMind(data.nodes);
  setStatus("保存データを読み込みました");
}

themeInput.addEventListener("keydown", async (e) => {
  if (isImeComposing(e)) return;
  if (e.key !== "Enter") return;
  e.preventDefault();
  const theme = themeInput.value.trim();
  if (!theme) {
    setStatus("テーマを入力してください", true);
    return;
  }
  try {
    await generateFromTheme(theme);
  } catch (err) {
    setStatus(err.message || "生成処理でエラーが発生しました", true);
  }
});

saveBtn.addEventListener("click", async () => {
  try {
    await saveMind();
  } catch (err) {
    setStatus(err.message || "保存処理でエラーが発生しました", true);
  }
});

loadBtn.addEventListener("click", async () => {
  try {
    await loadMind();
  } catch (err) {
    setStatus(err.message || "読み込み処理でエラーが発生しました", true);
  }
});

bindHotkeys();
bindDoubleClickExpand();
loadMind().catch(() => createMind([{ id: "root", isroot: true, topic: "MindEdit" }]));
