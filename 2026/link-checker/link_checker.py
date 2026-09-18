"""
link_checker.py
指定したWebサイトを起点に、リンクを再帰的にたどってリンク切れを検出するツール

使い方:
    python link_checker.py https://example.com

特徴:
    - サイト内（同一ドメイン）は指定階層まで再帰的にクロール
    - 外部ドメインへのリンクは生死チェックのみ行い、再帰はしない
    - リクエスト間隔にランダムなゆらぎを持たせ、サーバー負荷を抑える
    - 取得済みページは cache/ 配下に保存し、同じURLを再取得しない
    - 結果は CSV に出力
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

CACHE_DIR = Path("cache")
MANIFEST_PATH = CACHE_DIR / "manifest.json"
WAIT_TIME = (0.5, 1.5)  # リクエスト間の待機秒数の範囲（最小, 最大）
TIMEOUT = 5.0  # リクエストタイムアウト秒数
USER_AGENT = "link-checker/1.0"  # 送信するUser-Agent
MAX_DEPTH = 2  # 最大再帰の深さ
EXCLUDE_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".zip", ".svg", ".ico", ".mp4", ".mp3")  # ダウンロードしない拡張子


@dataclass
class LinkResult:
    """"結果を保持するデータクラス"""
    source_page: str
    link_url: str
    status: str          # "OK" / "NG" / "SKIP(external-not-checked)" など
    status_code: str      # 取得できたHTTPステータスコード（文字列。エラー時は空）
    error: str = ""


@dataclass
class CrawlStats:
    """クロールの統計情報を保持するデータクラス"""
    pages_crawled: int = 0
    links_checked: int = 0
    broken_links: int = 0


# --- キャッシュ（URL -> ローカルファイル の対応を manifest.json で管理） -----------

@dataclass
class UrlCache:
    """キャッシュの状態を保持するだけのデータ。処理は関数側で行う"""
    cache_dir: Path
    manifest_path: Path
    manifest: dict[str, str]


def cache_init(cache_dir: Path = CACHE_DIR) -> UrlCache:
    """キャッシュ用ディレクトリを用意し、既存の manifest.json があれば読み込む"""
    manifest_path = cache_dir / "manifest.json"
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return UrlCache(cache_dir=cache_dir, manifest_path=manifest_path, manifest=manifest)


def cache_hash_name(url: str) -> str:
    """URLをSHA-256でハッシュ化し、キャッシュ用のファイル名を作る"""
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return f"{digest}.html"


def cache_get(cache: UrlCache, url: str) -> str | None:
    """キャッシュ済みならページ本文（HTML）を返す。なければ None"""
    filename = cache.manifest.get(url)
    if filename is None:
        return None
    path = cache.cache_dir / filename
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def cache_put(cache: UrlCache, url: str, html: str) -> None:
    """取得したHTMLをファイルに保存し、manifestに対応関係を記録する"""
    filename = cache_hash_name(url)
    path = cache.cache_dir / filename
    path.write_text(html, encoding="utf-8")
    cache.manifest[url] = filename
    cache_save_manifest(cache)


def cache_save_manifest(cache: UrlCache) -> None:
    """URLとキャッシュファイル名の対応表をmanifest.jsonに書き出す"""
    cache.manifest_path.write_text(
        json.dumps(cache.manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# --- リンクチェック本体 ---------------------------------------------------------

@dataclass
class LinkChecker:
    """クロール対象や動作パラメータ、進行状況を保持するだけのデータ。処理は関数側で行う"""
    start_url: str
    base_domain: str
    max_depth: int
    session: requests.Session
    cache: UrlCache
    visited_pages: set[str] = field(default_factory=set)
    checked_links: dict[str, tuple[str, str, str]] = field(default_factory=dict)  # url -> (status, code, error)
    results: list[LinkResult] = field(default_factory=list)
    stats: CrawlStats = field(default_factory=CrawlStats)


def checker_init(start_url: str) -> LinkChecker:
    """クロール対象や動作パラメータを受け取り、内部状態を初期化する"""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    return LinkChecker(
        start_url=start_url,
        base_domain=urlparse(start_url).netloc,
        max_depth=MAX_DEPTH,
        session=session,
        cache=cache_init(),
    )


# --- ユーティリティ ---------------------------------------------------

def normalize_url(url: str) -> str:
    """URL末尾のフラグメント（#以降）を取り除き、同一URLとして扱えるようにする"""
    url, _ = urldefrag(url)
    return url


def is_internal(checker: LinkChecker, url: str) -> bool:
    """起点URLと同じドメインかどうかを判定する（サイト内リンクの再帰対象判定に使用）"""
    return urlparse(url).netloc == checker.base_domain


def is_excluded(url: str) -> bool:
    """グローバル定数EXCLUDE_EXTENSIONSに該当し、ダウンロード対象外かどうかを判定する"""
    path = urlparse(url).path.lower()
    return path.endswith(EXCLUDE_EXTENSIONS)


def sleep_random() -> None:
    """グローバル定数WAIT_TIMEの範囲でランダムに待機し、サーバーへの負荷を抑える"""
    min_wait, max_wait = WAIT_TIME
    time.sleep(random.uniform(min_wait, max_wait))


# --- HTTP まわり --------------------------------------------------------

def fetch_page(checker: LinkChecker, url: str) -> tuple[str | None, str, str]:
    """ページ本文を取得する。キャッシュがあればそれを使う。

    戻り値: (html_or_None, status_code_str, error_str)
    """
    cached = cache_get(checker.cache, url)
    if cached is not None:
        print(f"[CACHE] {url}")
        return cached, "CACHED", ""

    try:
        sleep_random()
        resp = checker.session.get(url, timeout=TIMEOUT)
        code = str(resp.status_code)
        if resp.status_code >= 400:
            return None, code, f"HTTP {code}"
        html = resp.text
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type or content_type == "":
            cache_put(checker.cache, url, html)
        return html, code, ""
    except requests.RequestException as e:
        return None, "", str(e)


def check_link_status(checker: LinkChecker, url: str) -> tuple[str, str]:
    """リンク先の生死をチェックする。戻り値: (status_code_str, error_str)"""
    try:
        sleep_random()
        resp = checker.session.head(url, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code >= 400 or resp.status_code == 405:
            # HEADが許可されていない/失敗した場合はGETでフォールバック
            resp = checker.session.get(url, timeout=TIMEOUT, allow_redirects=True, stream=True)
            resp.close()
        return str(resp.status_code), ""
    except requests.RequestException as e:
        return "", str(e)


# --- クロール本体 --------------------------------------------------------

def crawl(checker: LinkChecker) -> None:
    """起点URLから幅優先でサイト内ページを巡回し各ページのリンクをチェック"""
    queue: list[tuple[str, int]] = [(normalize_url(checker.start_url), 0)]
    queued: set[str] = {queue[0][0]}

    while queue:
        url, depth = queue.pop(0)
        if url in checker.visited_pages:
            continue
        checker.visited_pages.add(url)

        print(f"[CRAWL] depth={depth} {url}")
        html, code, error = fetch_page(checker, url)
        checker.stats.pages_crawled += 1

        if html is None:
            checker.results.append(
                LinkResult(
                    source_page="(start)" if depth == 0 else "(direct fetch)",
                    link_url=url,
                    status="NG",
                    status_code=code,
                    error=error,
                )
            )
            checker.stats.broken_links += 1
            continue

        soup = BeautifulSoup(html, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            raw_href = str(a_tag["href"]).strip()
            if not raw_href or raw_href.startswith(("mailto:", "tel:", "javascript:")):
                continue

            link_url = normalize_url(urljoin(url, raw_href))

            if is_excluded(link_url):
                continue

            check_and_record(checker, link_url, source_page=url)

            if is_internal(checker, link_url) and depth + 1 <= checker.max_depth:
                if link_url not in checker.visited_pages and link_url not in queued:
                    queue.append((link_url, depth + 1))
                    queued.add(link_url)


def check_and_record(checker: LinkChecker, link_url: str, source_page: str) -> None:
    """リンク先の生死をチェックし、結果をresultsに記録する（同一URLは再チェックせずキャッシュを使う）"""
    if link_url in checker.checked_links:
        status, code, error = checker.checked_links[link_url]
        checker.results.append(
            LinkResult(source_page=source_page, link_url=link_url, status=status, status_code=code, error=error)
        )
        return

    code, error = check_link_status(checker, link_url)
    checker.stats.links_checked += 1

    if code and int(code) < 400:
        status = "OK"
    else:
        status = "NG"
        checker.stats.broken_links += 1
        print(f"   [NG] {link_url} (code={code or '-'} error={error or '-'})")

    checker.checked_links[link_url] = (status, code, error)
    checker.results.append(
        LinkResult(source_page=source_page, link_url=link_url, status=status, status_code=code, error=error)
    )

# --- 出力 --------------------------------------------------------------

def write_reports(checker: LinkChecker, output_dir: Path) -> Path:
    """チェック結果をタイムスタンプ付きのCSVファイルに書き出す"""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"link_check_{timestamp}.csv"

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["source_page", "link_url", "status", "status_code", "error"])
        for r in checker.results:
            writer.writerow([r.source_page, r.link_url, r.status, r.status_code, r.error])

    return csv_path


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を定義し、解析結果を返す"""
    parser = argparse.ArgumentParser(description="再帰的にリンクをたどってリンク切れを検出するツール")
    parser.add_argument("start_url", help="クロールを開始するURL")
    parser.add_argument("--output", type=str, default="results", help="レポート出力先ディレクトリ（デフォルト: results）")
    return parser.parse_args()


def main() -> None:
    """コマンドライン引数を読み取り、クロール・チェック・レポート出力を実行する"""
    args = parse_args()
    checker = checker_init(start_url=args.start_url)
    crawl(checker)
    csv_path = write_reports(checker, Path(args.output))

    print("\n=== 完了 ===")
    print(f"クロールしたページ数: {checker.stats.pages_crawled}")
    print(f"チェックしたリンク数: {checker.stats.links_checked}")
    print(f"リンク切れ件数      : {checker.stats.broken_links}")
    print(f"CSV : {csv_path}")


if __name__ == "__main__":
    main()
