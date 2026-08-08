#!/usr/bin/env python3
"""文字起こしTXTへ句読点と段落を加え、原文を保った整形版を作る。"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests


API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"
MAX_RETRIES = 4
TIMESTAMP = re.compile(r"^\[\d{2}:\d{2}:\d{2} - \d{2}:\d{2}:\d{2}\]", re.MULTILINE)

SYSTEM_PROMPT = """あなたは日本語の文字起こしを整形する校正者です。
入力された文字列の語句、表記、数値、固有名詞は一文字も変更せず、追加・削除・要約・言い換えを絶対にしないでください。
行うのは次の二つだけです。
1. 文意に沿って日本語の句読点（、。）と必要最小限の疑問符を加える。
2. 話題・話者・場面のまとまりごとに空行を1行入れる。
先頭の [HH:MM:SS - HH:MM:SS] は必ずそのまま残してください。
説明、見出し、Markdownのコードフェンスを加えず、整形後の本文だけを返してください。"""


class FormatError(RuntimeError):
    pass


def atomic_write(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def split_timestamp_chunks(text: str) -> list[str]:
    starts = [match.start() for match in TIMESTAMP.finditer(text)]
    if not starts or starts[0] != 0:
        raise FormatError("先頭に [HH:MM:SS - HH:MM:SS] 形式の時刻がありません。")
    return [text[start:end].strip() for start, end in zip(starts, starts[1:] + [len(text)])]


def comparable(text: str) -> str:
    return "".join(
        character
        for character in text
        if not character.isspace() and not unicodedata.category(character).startswith("P")
    )


def validate(original: str, formatted: str) -> None:
    if not TIMESTAMP.match(formatted):
        raise FormatError("整形結果の先頭タイムスタンプが失われました。")
    if comparable(original) != comparable(formatted):
        raise FormatError("整形結果に句読点・改行以外の変更が含まれています。")


def is_formatting(character: str) -> bool:
    return character.isspace() or unicodedata.category(character).startswith("P")


def keep_inserted_formatting(original: str, candidate: str) -> tuple[str, int, int]:
    """候補のうち、原文への句読点・空白の挿入だけを安全に採用する。"""
    matcher = difflib.SequenceMatcher(a=original, b=candidate, autojunk=False)
    parts: list[str] = []
    inserted = 0
    ignored_changes = 0
    for tag, source_start, source_end, candidate_start, candidate_end in matcher.get_opcodes():
        if tag == "equal":
            parts.append(original[source_start:source_end])
        elif tag == "insert":
            addition = candidate[candidate_start:candidate_end]
            if all(is_formatting(character) for character in addition):
                parts.append(addition)
                inserted += len(addition)
            else:
                ignored_changes += 1
        else:
            # 置換・削除は原文をそのまま残す。候補の語句変更は絶対に採用しない。
            parts.append(original[source_start:source_end])
            ignored_changes += 1
    return "".join(parts).strip(), inserted, ignored_changes


def request_format(session: requests.Session, api_key: str, text: str) -> str:
    payload = {
        "model": MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = session.post(API_URL, headers=headers, json=payload, timeout=(30, 600))
        except requests.RequestException as exc:
            if attempt >= MAX_RETRIES:
                raise FormatError(f"OpenRouterへの接続に失敗しました: {exc}") from exc
        else:
            if response.ok:
                try:
                    content = response.json()["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError, ValueError) as exc:
                    raise FormatError("OpenRouterの整形応答を読み取れませんでした。") from exc
                if not isinstance(content, str):
                    raise FormatError("OpenRouterの整形応答がテキストではありません。")
                return content.strip()
            if response.status_code not in {408, 429, 500, 502, 503, 504} or attempt >= MAX_RETRIES:
                raise FormatError(f"OpenRouter APIエラー ({response.status_code}): {response.text[:500]}")

        delay = min(60, 2**attempt)
        print(f"  一時エラーのため{delay}秒後に再試行します", flush=True)
        time.sleep(delay)
    raise AssertionError("retry loop ended unexpectedly")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="文字起こしTXTに句読点と段落を加えます。")
    parser.add_argument("input", type=Path, help="整形するTXT")
    parser.add_argument("-o", "--output", type=Path, help="出力先（既定: <入力名>-formatted.txt）")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.input.resolve()
    if not source.is_file():
        print(f"エラー: ファイルが見つかりません: {source}", file=sys.stderr)
        return 1
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("エラー: 環境変数 OPENROUTER_API_KEY が設定されていません。", file=sys.stderr)
        return 1

    output = args.output.resolve() if args.output else source.with_name(f"{source.stem}-formatted.txt")
    original = source.read_text(encoding="utf-8").strip()
    chunks = split_timestamp_chunks(original)
    fingerprint = hashlib.sha256(original.encode("utf-8")).hexdigest()[:16]
    cache_dir = source.parent / ".format-work" / source.name / fingerprint
    cache_dir.mkdir(parents=True, exist_ok=True)
    formatted_chunks: list[str] = []

    with requests.Session() as session:
        for index, chunk in enumerate(chunks, start=1):
            cache_path = cache_dir / f"chunk_{index:04d}.txt"
            if cache_path.exists():
                formatted = cache_path.read_text(encoding="utf-8").strip()
                validate(chunk, formatted)
                print(f"[{index}/{len(chunks)}] 保存済み整形結果を使用", flush=True)
            else:
                print(f"[{index}/{len(chunks)}] 句読点・段落を整形中", flush=True)
                formatted = request_format(session, api_key, chunk)
                try:
                    validate(chunk, formatted)
                except FormatError:
                    formatted, inserted, ignored_changes = keep_inserted_formatting(chunk, formatted)
                    if not inserted:
                        raise FormatError(
                            "整形応答に安全に採用できる句読点・改行がありませんでした。"
                        )
                    validate(chunk, formatted)
                    print(
                        f"  語句変更を無視し、句読点・改行{inserted}文字だけを採用しました "
                        f"(変更候補 {ignored_changes}件)",
                        flush=True,
                    )
                atomic_write(cache_path, formatted + "\n")
            formatted_chunks.append(formatted)

    atomic_write(output, "\n\n".join(formatted_chunks).rstrip() + "\n")
    print(f"書き出し完了: {output}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FormatError, KeyboardInterrupt) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
