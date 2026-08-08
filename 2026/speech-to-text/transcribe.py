#!/usr/bin/env python3
"""OpenRouterのWhisperを使い、長時間のMP3を分割して文字起こしする。"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests


MODEL = "openai/whisper-large-v3-turbo"
API_URL = "https://openrouter.ai/api/v1/audio/transcriptions"
DEFAULT_CHUNK_MINUTES = 10
DEFAULT_MAX_RETRIES = 5
RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}


class TranscriptionError(RuntimeError):
    """利用者に表示できる文字起こしエラー。"""


def natural_sort_key(path: Path) -> list[tuple[int, object]]:
    """数字部分を数値として比較する自然順ソートキーを返す。"""
    parts = re.split(r"(\d+)", path.name.lower())
    return [(0, int(part)) if part.isdigit() else (1, part) for part in parts]


def format_time(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def atomic_write_text(path: Path, text: str) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    os.replace(tmp_path, path)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2))


def run_command(command: list[str], description: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise TranscriptionError(
            f"{command[0]} が見つかりません。FFmpegをインストールしてください。"
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise TranscriptionError(f"{description}に失敗しました: {detail}") from exc


def probe_duration(path: Path) -> float:
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        f"音声時間の取得 ({path.name})",
    )
    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise TranscriptionError(f"音声時間を取得できませんでした: {path}") from exc


def source_fingerprint(path: Path, chunk_seconds: int) -> str:
    stat = path.stat()
    value = f"{path.resolve()}\0{stat.st_size}\0{stat.st_mtime_ns}\0{chunk_seconds}\0{MODEL}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def prepare_chunks(mp3_path: Path, chunk_minutes: int) -> tuple[Path, list[dict[str, Any]]]:
    chunk_seconds = chunk_minutes * 60
    fingerprint = source_fingerprint(mp3_path, chunk_seconds)
    work_dir = mp3_path.parent / ".transcribe-work" / mp3_path.name / fingerprint
    manifest_path = work_dir / "manifest.json"

    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            chunks = manifest["chunks"]
            if manifest.get("mode") == "one-at-a-time" and chunks:
                return work_dir, chunks
        except (OSError, KeyError, TypeError, json.JSONDecodeError):
            pass

    work_dir.mkdir(parents=True, exist_ok=True)
    for stale_path in work_dir.glob("chunk_*.mp3"):
        stale_path.unlink()

    total_duration = probe_duration(mp3_path)
    chunks = []
    for index in range(math.ceil(total_duration / chunk_seconds)):
        offset = index * chunk_seconds
        duration = min(chunk_seconds, total_duration - offset)
        chunks.append(
            {"file": f"chunk_{index:04d}.mp3", "offset": offset, "duration": duration}
        )

    atomic_write_json(
        manifest_path,
        {
            "source": mp3_path.name,
            "model": MODEL,
            "chunk_minutes": chunk_minutes,
            "mode": "one-at-a-time",
            "chunks": chunks,
        },
    )
    return work_dir, chunks


def create_chunk_file(mp3_path: Path, chunk_path: Path, offset: float, duration: float) -> None:
    """空き容量を抑えるため、現在処理する1チャンクだけを生成する。"""
    if chunk_path.is_file():
        return
    print(f"    分割音声を作成中 ({format_time(offset)} から)", flush=True)
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{offset:.3f}",
            "-i",
            str(mp3_path),
            "-t",
            f"{duration:.3f}",
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-b:a",
            "32k",
            str(chunk_path),
        ],
        f"分割音声の作成 ({mp3_path.name})",
    )


def retry_delay(response: requests.Response | None, attempt: int) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(120.0, max(0.0, float(retry_after)))
            except ValueError:
                pass
    return min(60.0, (2**attempt) + random.random())


def transcribe_chunk(
    chunk_path: Path,
    api_key: str,
    max_retries: int,
    session: requests.Session,
) -> dict[str, Any]:
    encoded_audio = base64.b64encode(chunk_path.read_bytes()).decode("ascii")
    payload = {
        "model": MODEL,
        "language": "ja",
        "input_audio": {"data": encoded_audio, "format": "mp3"},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    for attempt in range(max_retries + 1):
        response: requests.Response | None = None
        try:
            response = session.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=(30, 600),
            )
        except requests.RequestException as exc:
            if attempt >= max_retries:
                raise TranscriptionError(f"OpenRouter APIへの接続に失敗しました: {exc}") from exc
        else:
            if response.ok:
                try:
                    result = response.json()
                except requests.JSONDecodeError as exc:
                    raise TranscriptionError("OpenRouter APIから不正なJSONが返されました。") from exc
                if not isinstance(result, dict) or not isinstance(result.get("text"), str):
                    raise TranscriptionError("OpenRouter APIの応答に文字起こし結果がありません。")
                return result

            if response.status_code not in RETRYABLE_STATUS_CODES or attempt >= max_retries:
                body = response.text[:1000].strip()
                raise TranscriptionError(
                    f"OpenRouter APIエラー ({response.status_code}): {body or '詳細なし'}"
                )

        delay = retry_delay(response, attempt)
        print(f"    一時エラーのため{delay:.1f}秒後に再試行します ({attempt + 1}/{max_retries})", flush=True)
        time.sleep(delay)

    raise AssertionError("retry loop ended unexpectedly")


def render_result(result: dict[str, Any], offset: float, duration: float) -> str:
    segments = result.get("segments")
    if isinstance(segments, list) and segments:
        lines = []
        for segment in segments:
            try:
                start = offset + float(segment["start"])
                end = offset + float(segment["end"])
                text = str(segment["text"]).strip()
            except (KeyError, TypeError, ValueError):
                continue
            if text:
                lines.append(f"[{format_time(start)} - {format_time(end)}] {text}")
        if lines:
            return "\n".join(lines)

    text = result["text"].strip()
    return f"[{format_time(offset)} - {format_time(offset + duration)}]\n{text}"


def transcribe_file(
    mp3_path: Path,
    *,
    chunk_minutes: int = DEFAULT_CHUNK_MINUTES,
    max_retries: int = DEFAULT_MAX_RETRIES,
    force: bool = False,
) -> Path:
    mp3_path = mp3_path.resolve()
    if not mp3_path.is_file():
        raise TranscriptionError(f"ファイルが見つかりません: {mp3_path}")
    if mp3_path.suffix.lower() != ".mp3":
        raise TranscriptionError(f"MP3ファイルではありません: {mp3_path}")

    output_path = mp3_path.with_suffix(".txt")
    if output_path.exists() and not force:
        print(f"スキップ（出力済み）: {output_path.name}", flush=True)
        return output_path

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise TranscriptionError("環境変数 OPENROUTER_API_KEY が設定されていません。")

    print(f"処理開始: {mp3_path.name}", flush=True)
    work_dir, chunks = prepare_chunks(mp3_path, chunk_minutes)
    rendered_chunks: list[str] = []

    with requests.Session() as session:
        for index, chunk in enumerate(chunks, start=1):
            result_path = work_dir / f"result_{index - 1:04d}.json"
            chunk_path = work_dir / chunk["file"]
            if result_path.exists():
                try:
                    result = json.loads(result_path.read_text(encoding="utf-8"))
                    if not isinstance(result, dict) or not isinstance(result.get("text"), str):
                        raise ValueError
                    print(f"  [{index}/{len(chunks)}] 保存済み結果を使用", flush=True)
                    chunk_path.unlink(missing_ok=True)
                except (OSError, ValueError, json.JSONDecodeError):
                    result_path.unlink(missing_ok=True)
                    result = None
            else:
                result = None

            if result is None:
                print(f"  [{index}/{len(chunks)}] 文字起こし中", flush=True)
                create_chunk_file(
                    mp3_path, chunk_path, float(chunk["offset"]), float(chunk["duration"])
                )
                result = transcribe_chunk(chunk_path, api_key, max_retries, session)
                atomic_write_json(result_path, result)
                chunk_path.unlink(missing_ok=True)

            rendered_chunks.append(
                render_result(result, float(chunk["offset"]), float(chunk["duration"]))
            )

    atomic_write_text(output_path, "\n\n".join(rendered_chunks).rstrip() + "\n")
    print(f"書き出し完了: {output_path}", flush=True)
    return output_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MP3を分割し、OpenRouterのWhisperで文字起こしします。"
    )
    parser.add_argument("mp3", type=Path, help="文字起こしするMP3ファイル")
    parser.add_argument(
        "--chunk-minutes",
        type=int,
        default=DEFAULT_CHUNK_MINUTES,
        help=f"分割する長さ（分、既定: {DEFAULT_CHUNK_MINUTES}）",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"一時エラー時の最大再試行回数（既定: {DEFAULT_MAX_RETRIES}）",
    )
    parser.add_argument("--force", action="store_true", help="既存のTXTを上書きする")
    args = parser.parse_args(argv)
    if args.chunk_minutes <= 0:
        parser.error("--chunk-minutes は1以上にしてください。")
    if args.max_retries < 0:
        parser.error("--max-retries は0以上にしてください。")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        transcribe_file(
            args.mp3,
            chunk_minutes=args.chunk_minutes,
            max_retries=args.max_retries,
            force=args.force,
        )
    except TranscriptionError as exc:
        print(f"エラー: {exc}", file=sys.stderr, flush=True)
        return 1
    except KeyboardInterrupt:
        print("\n中断しました。次回は保存済みの続きから再開します。", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
