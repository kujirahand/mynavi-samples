#!/usr/bin/env python3
"""同じフォルダのMP3を自然順で一つずつ文字起こしする。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from transcribe import DEFAULT_CHUNK_MINUTES, DEFAULT_MAX_RETRIES, natural_sort_key


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="フォルダ直下の全MP3を自然順で逐次文字起こしします。"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="MP3があるフォルダ（既定: カレントフォルダ）",
    )
    parser.add_argument(
        "--chunk-minutes", type=int, default=DEFAULT_CHUNK_MINUTES, help="分割する長さ（分）"
    )
    parser.add_argument(
        "--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help="最大再試行回数"
    )
    parser.add_argument("--force", action="store_true", help="既存のTXTを上書きする")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="あるファイルが失敗しても次のファイルへ進む",
    )
    args = parser.parse_args(argv)
    if args.chunk_minutes <= 0:
        parser.error("--chunk-minutes は1以上にしてください。")
    if args.max_retries < 0:
        parser.error("--max-retries は0以上にしてください。")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    directory = args.directory.resolve()
    if not directory.is_dir():
        print(f"エラー: フォルダが見つかりません: {directory}", file=sys.stderr)
        return 1

    mp3_files = sorted(directory.glob("*.mp3"), key=natural_sort_key)
    if not mp3_files:
        print(f"エラー: MP3ファイルがありません: {directory}", file=sys.stderr)
        return 1

    print("処理順:", flush=True)
    for index, path in enumerate(mp3_files, start=1):
        print(f"  {index:2d}. {path.name}", flush=True)

    script_path = Path(__file__).resolve().with_name("transcribe.py")
    failed: list[str] = []
    for index, mp3_path in enumerate(mp3_files, start=1):
        print(f"\n=== {index}/{len(mp3_files)}: {mp3_path.name} ===", flush=True)
        command = [
            sys.executable,
            str(script_path),
            str(mp3_path),
            "--chunk-minutes",
            str(args.chunk_minutes),
            "--max-retries",
            str(args.max_retries),
        ]
        if args.force:
            command.append("--force")
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            failed.append(mp3_path.name)
            if not args.continue_on_error:
                print(
                    f"エラー: {mp3_path.name} で停止しました。再実行すると続きから再開します。",
                    file=sys.stderr,
                )
                return result.returncode

    if failed:
        print(f"\n完了しましたが、失敗したファイルがあります: {', '.join(failed)}", file=sys.stderr)
        return 1

    print(f"\n全{len(mp3_files)}ファイルの処理が完了しました。", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
