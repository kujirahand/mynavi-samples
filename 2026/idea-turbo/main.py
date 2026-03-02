from __future__ import annotations

import random
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import tomllib

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def load_settings() -> dict:
    """setting.tomlを読み込み、なければデフォルト値を使う。"""
    default = {
        "app": {"idle_seconds": 20, "sakura_probability": 0.45},
        "ollama": {
            "model": "gemma3:4b",
            "endpoint": "http://127.0.0.1:11434/api/generate",
            "temperature": 0.9,
        },
        "prompt": {
            "praise": (
                "あなたは超ハイテンションなアイデア応援AIです。\n"
                "以下のアイデアを日本語で全力で褒めてください。\n"
                "タイトル: {title}\n"
                "ユーザーのアイデア: {idea}"
            ),
            "suggest": (
                "あなたは優秀な発想パートナーです。\n"
                "タイトルと既存アイデアを踏まえ、次の一歩になる新しい案を1つ提案してください。\n"
                "タイトル: {title}\n"
                "既存アイデア:\n{ideas}"
            ),
        },
    }

    settings_path = BASE_DIR / "setting.toml"
    if not settings_path.exists():
        return default

    with settings_path.open("rb") as f:
        loaded = tomllib.load(f)

    # デフォルト値とマージして、設定漏れでも動作させる
    for section, values in default.items():
        loaded.setdefault(section, {})
        for key, value in values.items():
            loaded[section].setdefault(key, value)
    return loaded


SETTINGS = load_settings()
app = FastAPI(title="idea-turbo")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# タイトルごとの入力履歴をメモリで持つ
SESSION_STATE: Dict[str, List[str]] = {}


def sanitize_title(title: str) -> str:
    """ファイル名に使えない文字を置換して安全にする。"""
    normalized = title.strip()
    if not normalized:
        raise ValueError("タイトルが空です")
    return re.sub(r"[\\/:*?\"<>|]", "_", normalized)


def log_path_for_title(title: str) -> Path:
    return DATA_DIR / f"{sanitize_title(title)}.txt"


def append_log(title: str, speaker: str, message: str) -> None:
    """会話を`data/{タイトル}.txt`へ追記する。"""
    path = log_path_for_title(title)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"[{now}] {speaker}: {message}\n")


async def generate_with_ollama(prompt: str) -> str:
    """Ollama APIを呼び出してテキストを生成する。"""
    payload = {
        "model": SETTINGS["ollama"]["model"],
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": SETTINGS["ollama"]["temperature"],
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(SETTINGS["ollama"]["endpoint"], json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        # ローカルLLM未起動でもUIが止まらないように、代替メッセージを返す
        return f"Ollamaに接続できませんでした。起動後に再実行してください。詳細: {exc}"

    return data.get("response", "応答を取得できませんでした。")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "idle_seconds": SETTINGS["app"]["idle_seconds"],
            "model_name": SETTINGS["ollama"]["model"],
        },
    )


@app.post("/start")
async def start_session(request: Request):
    payload = await request.json()
    title = (payload.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="タイトルは必須です")

    safe_title = sanitize_title(title)
    SESSION_STATE.setdefault(safe_title, [])
    append_log(safe_title, "SYSTEM", f"セッション開始: {title}")
    return JSONResponse({"ok": True, "title": safe_title})


@app.post("/idea")
async def submit_idea(request: Request):
    payload = await request.json()
    title = (payload.get("title") or "").strip()
    idea = (payload.get("idea") or "").strip()
    if not title or not idea:
        raise HTTPException(status_code=400, detail="タイトルとアイデアが必要です")

    safe_title = sanitize_title(title)
    SESSION_STATE.setdefault(safe_title, []).append(idea)

    append_log(safe_title, "USER", idea)

    prompt = SETTINGS["prompt"]["praise"].format(title=safe_title, idea=idea)
    ai_message = await generate_with_ollama(prompt)
    append_log(safe_title, "AI", ai_message)

    sakura = random.random() < float(SETTINGS["app"]["sakura_probability"])
    return JSONResponse({"message": ai_message, "sakura": sakura})


@app.post("/suggest")
async def suggest_idea(request: Request):
    payload = await request.json()
    title = (payload.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="タイトルが必要です")

    safe_title = sanitize_title(title)
    ideas = SESSION_STATE.get(safe_title, [])

    if ideas:
        ideas_text = "\n".join(f"- {i}" for i in ideas[-10:])
    else:
        ideas_text = "- まだ入力なし"

    prompt = SETTINGS["prompt"]["suggest"].format(title=safe_title, ideas=ideas_text)
    ai_message = await generate_with_ollama(prompt)
    append_log(safe_title, "AI-SUGGEST", ai_message)

    return JSONResponse({"message": ai_message})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
