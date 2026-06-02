from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from src.discovery_models import CandidatePaper


SUPPORTED_CLIPPING_EXTENSIONS = {".md", ".html", ".txt"}
URL_PATTERN = re.compile(r"https?://\S+")
HTML_TITLE_PATTERN = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def ingest_clippings(clippings_dir: Path) -> list[CandidatePaper]:
    if not clippings_dir.exists() or not clippings_dir.is_dir():
        return []

    candidates = []
    for path in sorted(clippings_dir.iterdir()):
        if path.suffix.lower() not in SUPPORTED_CLIPPING_EXTENSIONS or not path.is_file():
            continue
        candidates.append(parse_clipping(path))
    return candidates


def parse_clipping(path: Path) -> CandidatePaper:
    text = path.read_text(encoding="utf-8", errors="ignore")
    title = extract_title(text, path)
    url = extract_url(text)
    timestamp = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    return CandidatePaper(
        title=title,
        source="clipping",
        origin="user_clipping",
        url=url,
        timestamp=timestamp,
        abstract=first_paragraph(text),
    )


def extract_title(text: str, path: Path) -> str:
    html_match = HTML_TITLE_PATTERN.search(text)
    if html_match:
        return clean_text(html_match.group(1))
    for line in text.splitlines():
        cleaned = clean_text(line.strip("# "))
        if cleaned and not cleaned.startswith("http"):
            return cleaned
    return path.stem


def extract_url(text: str) -> str | None:
    match = URL_PATTERN.search(text)
    return match.group(0).rstrip(").,]") if match else None


def first_paragraph(text: str, limit: int = 1000) -> str:
    for paragraph in text.split("\n\n"):
        cleaned = clean_text(paragraph)
        if cleaned and not cleaned.startswith("http"):
            return cleaned[:limit]
    return ""


def clean_text(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()
