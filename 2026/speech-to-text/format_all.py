#!/usr/bin/env python3
"""フォルダ直下の文字起こしTXTを自然順で整形する。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from transcribe import natural_sort_key


def main() -> int:
    parser = argparse.ArgumentParser(description="全ての文字起こしTXTを句読点・段落整形します。")
    parser.add_argument("directory", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not directory.is_dir():
        print(f"エラー: フォルダが見つかりません: {directory}", file=sys.stderr)
        return 1

    sources = sorted(
        (
            path
            for path in directory.glob("*.txt")
            if not path.stem.endswith("-formatted")
        ),
        key=natural_sort_key,
    )
    if not sources:
        print("整形対象のTXTがありません。", file=sys.stderr)
        return 1

    script = Path(__file__).resolve().with_name("format_transcript.py")
    for index, source in enumerate(sources, start=1):
        output = source.with_name(f"{source.stem}-formatted.txt")
        if output.exists():
            print(f"[{index}/{len(sources)}] スキップ（整形済み）: {source.name}", flush=True)
            continue
        print(f"\n=== {index}/{len(sources)}: {source.name} ===", flush=True)
        result = subprocess.run([sys.executable, str(script), str(source)], check=False)
        if result.returncode:
            print(f"エラー: {source.name} で停止しました。再実行すると続きから再開します。", file=sys.stderr)
            return result.returncode

    print(f"\n全{len(sources)}ファイルの整形が完了しました。", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
