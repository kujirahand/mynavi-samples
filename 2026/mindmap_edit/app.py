import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request
from openai import OpenAI

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"
SAVE_FILE = DATA_DIR / "mindmap_latest.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def _extract_json_object(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response.")
    return json.loads(match.group(0))


def _extract_json_array(text: str) -> list[Any]:
    match = re.search(r"\[.*\]", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in model response.")
    return json.loads(match.group(0))


def _safe_topic(text: Any, fallback: str) -> str:
    cleaned = str(text).strip()
    return cleaned[:80] if cleaned else fallback


def _model_text(prompt: str, temperature: float = 0.7) -> str:
    if client is None:
        raise ValueError("OPENAI_API_KEY is not set.")

    # Newer SDKs expose Responses API.
    if hasattr(client, "responses"):
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=prompt,
            temperature=temperature,
        )
        return response.output_text or ""

    # Backward-compatible fallback for older SDK shapes.
    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    if not completion.choices:
        return ""
    return completion.choices[0].message.content or ""


def _build_jsmind_nodes(root_topic: str, tree_children: list[dict[str, Any]]) -> list[dict[str, str]]:
    nodes: list[dict[str, str]] = [{"id": "root", "isroot": True, "topic": _safe_topic(root_topic, "Main Topic")}]

    for first_level in tree_children:
        parent_id = str(uuid.uuid4())
        parent_topic = _safe_topic(first_level.get("topic"), "Idea")
        nodes.append({"id": parent_id, "parentid": "root", "topic": parent_topic})

        raw_children = first_level.get("children", [])
        if not isinstance(raw_children, list):
            continue

        for child_topic in raw_children[:8]:
            nodes.append(
                {
                    "id": str(uuid.uuid4()),
                    "parentid": parent_id,
                    "topic": _safe_topic(child_topic, "Sub idea"),
                }
            )
    return nodes


def _fallback_map(theme: str) -> list[dict[str, str]]:
    t = _safe_topic(theme, "MindEdit Theme")
    return [
        {"id": "root", "isroot": True, "topic": t},
        {"id": "a", "parentid": "root", "topic": "Core Concepts"},
        {"id": "b", "parentid": "root", "topic": "Practical Use Cases"},
        {"id": "c", "parentid": "root", "topic": "Challenges"},
        {"id": "d", "parentid": "a", "topic": "Definitions"},
        {"id": "e", "parentid": "a", "topic": "Key Components"},
        {"id": "f", "parentid": "b", "topic": "Real-world Examples"},
        {"id": "g", "parentid": "c", "topic": "Risks"},
    ]


def _generate_structure(theme: str) -> list[dict[str, str]]:
    if client is None:
        return _fallback_map(theme)

    prompt = (
        "You are generating a mind map. "
        "Return only valid JSON in this exact format: "
        '{"root":"...", "children":[{"topic":"...", "children":["...","..."]}]}. '
        "No markdown. Keep it concise. "
        f"Theme: {theme}"
    )
    text = _model_text(prompt, temperature=0.7)
    obj = _extract_json_object(text)
    root = _safe_topic(obj.get("root", theme), theme)
    children = obj.get("children", [])
    if not isinstance(children, list):
        raise ValueError("Invalid children format.")
    return _build_jsmind_nodes(root, children[:8])


def _expand_node_ideas(node_topic: str, parent_topic: str | None = None) -> list[str]:
    if client is None:
        return [
            f"{node_topic} - Detail 1",
            f"{node_topic} - Detail 2",
            f"{node_topic} - Detail 3",
        ]

    relation = f" Parent topic: {parent_topic}." if parent_topic else ""
    prompt = (
        "Generate 3 to 6 concise child ideas for a mind map node. "
        "Return only a JSON array of strings, no markdown."
        f" Node topic: {node_topic}.{relation}"
    )
    text = _model_text(prompt, temperature=0.8)
    arr = _extract_json_array(text)
    ideas = []
    for item in arr[:6]:
        txt = _safe_topic(item, "")
        if txt:
            ideas.append(txt)
    return ideas or [f"{node_topic} - New idea"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    payload = request.get_json(silent=True) or {}
    theme = str(payload.get("theme", "")).strip()
    if not theme:
        return jsonify({"error": "Theme is required."}), 400

    try:
        nodes = _generate_structure(theme)
    except Exception as exc:
        return jsonify({"error": f"Failed to generate ideas: {exc}"}), 500

    return jsonify({"nodes": nodes})


@app.route("/api/expand", methods=["POST"])
def api_expand():
    payload = request.get_json(silent=True) or {}
    node_topic = str(payload.get("topic", "")).strip()
    parent_topic = payload.get("parentTopic")
    if not node_topic:
        return jsonify({"error": "Node topic is required."}), 400

    try:
        ideas = _expand_node_ideas(node_topic, parent_topic)
    except Exception as exc:
        return jsonify({"error": f"Failed to expand ideas: {exc}"}), 500

    return jsonify({"ideas": ideas})


@app.route("/api/save", methods=["POST"])
def api_save():
    payload = request.get_json(silent=True) or {}
    nodes = payload.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return jsonify({"error": "Valid nodes are required."}), 400

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    document = {
        "savedAt": datetime.utcnow().isoformat() + "Z",
        "nodes": nodes,
    }
    SAVE_FILE.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return jsonify({"message": "Saved", "savedAt": document["savedAt"]})


@app.route("/api/load", methods=["GET"])
def api_load():
    if not SAVE_FILE.exists():
        return jsonify({"nodes": []})

    try:
        payload = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
        nodes = payload.get("nodes", [])
        return jsonify({"nodes": nodes, "savedAt": payload.get("savedAt")})
    except Exception:
        return jsonify({"nodes": [], "savedAt": None})


if __name__ == "__main__":
    app.run(debug=True)
