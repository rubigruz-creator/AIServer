#!/usr/bin/env python3
"""
Сбор текста со своих сайтов → черновик prompts/knowledge/sites-scraped.md
Использование: python3 scripts/knowledge-scrape.py [--urls scripts/knowledge-urls.txt]
Требует ручной проверки перед model-create / knowledge-index.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_URLS = ROOT / "scripts" / "knowledge-urls.txt"
OUTPUT = ROOT / "prompts" / "knowledge" / "sites-scraped.md"
USER_AGENT = "AIServer-KnowledgeBot/1.0 (+internal; review before publish)"
TIMEOUT = 25


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "nav", "footer", "header", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "nav", "footer", "header", "noscript"):
            self._skip = max(0, self._skip - 1)
        if self._skip == 0 and tag in ("p", "h1", "h2", "h3", "h4", "li", "td", "th"):
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip == 0:
            text = data.strip()
            if text:
                self._chunks.append(text + " ")

    def text(self) -> str:
        raw = "".join(self._chunks)
        raw = re.sub(r"\s+", " ", raw)
        return raw.strip()


def load_urls(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def fetch_url(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=TIMEOUT) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        html = resp.read().decode(charset, errors="replace")
    parser = TextExtractor()
    parser.feed(html)
    return parser.text()


def main() -> int:
    ap = argparse.ArgumentParser(description="Scrape whitelist URLs to knowledge markdown")
    ap.add_argument("--urls", type=Path, default=DEFAULT_URLS)
    ap.add_argument("-o", "--output", type=Path, default=OUTPUT)
    ap.add_argument("--max-chars", type=int, default=4000, help="Max chars per URL")
    args = ap.parse_args()

    if not args.urls.is_file():
        print(f"URLs file not found: {args.urls}", file=sys.stderr)
        return 1

    urls = load_urls(args.urls)
    if not urls:
        print("No URLs in whitelist", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sections: list[str] = [
        "# Черновик с сайтов (требует проверки)",
        "",
        f"Сгенерировано: {now}",
        "",
        "> Не используйте без ревью. Удалите дубли, устаревшие цены, мусор из меню.",
        "",
    ]

    for url in urls:
        print(f"Fetching {url}...")
        try:
            text = fetch_url(url)
        except (URLError, TimeoutError, ValueError) as e:
            print(f"  skip: {e}", file=sys.stderr)
            sections.append(f"## {url}\n\n_Ошибка загрузки: {e}_\n")
            continue
        if len(text) > args.max_chars:
            text = text[: args.max_chars] + "…"
        sections.append(f"## {url}\n\n{text}\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(sections) + "\n", encoding="utf-8")
    print(f"Written {args.output} ({len(urls)} URLs)")
    print("Next: edit file, then ./scripts/knowledge-index.sh && ./scripts/model-create.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
