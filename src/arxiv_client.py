from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import ssl
import time
from urllib.parse import quote
from urllib.request import urlopen
import xml.etree.ElementTree as ET

import certifi
import yaml

from src.discovery_models import CandidatePaper


ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NAMESPACE = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}
DEFAULT_REQUEST_DELAY_SECONDS = 3.0


def load_arxiv_config(config_path: Path = Path("configs/paper_sources.yaml")) -> dict:
    default = {
        "arxiv": {
            "enabled": True,
            "query_mode": "date_window",
            "categories": ["cs.CL", "cs.LG", "cs.AI", "cs.CV", "stat.ML"],
            "lookback_days": 2,
            "max_results_per_category": 500,
            "max_pages_per_category": 2,
            "sort_by": "submittedDate",
            "sort_order": "descending",
            "sleep_seconds_between_queries": DEFAULT_REQUEST_DELAY_SECONDS,
        }
    }
    if not config_path.exists():
        return default
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else default


def fetch_recent_arxiv_papers(
    config_path: Path = Path("configs/paper_sources.yaml"),
) -> list[CandidatePaper]:
    config = load_arxiv_config(config_path).get("arxiv", {})
    if not config.get("enabled", True):
        return []

    lookback_days = int(config.get("lookback_days", 2))
    sleep_seconds = float(
        config.get("sleep_seconds_between_queries", DEFAULT_REQUEST_DELAY_SECONDS)
    )
    start_date = date.today() - timedelta(days=lookback_days)
    end_date = date.today()
    candidates: list[CandidatePaper] = []

    categories = list(config.get("categories", []))
    for category_index, category in enumerate(categories):
        if category_index > 0:
            time.sleep(max(sleep_seconds, DEFAULT_REQUEST_DELAY_SECONDS))
        entries = fetch_category_date_window(
            category=str(category),
            start_date=start_date,
            end_date=end_date,
            max_results_per_page=int(config.get("max_results_per_category", 500)),
            max_pages=int(config.get("max_pages_per_category", 2)),
            sort_by=str(config.get("sort_by", "submittedDate")),
            sort_order=str(config.get("sort_order", "descending")),
            sleep_seconds=max(sleep_seconds, DEFAULT_REQUEST_DELAY_SECONDS),
        )
        for candidate in entries:
            candidates.append(candidate)

    return candidates


def fetch_category_date_window(
    category: str,
    start_date: date,
    end_date: date,
    max_results_per_page: int,
    max_pages: int,
    sort_by: str,
    sort_order: str,
    sleep_seconds: float,
) -> list[CandidatePaper]:
    candidates: list[CandidatePaper] = []
    total_results: int | None = None

    for page_index in range(max_pages):
        if page_index > 0:
            time.sleep(sleep_seconds)

        start = page_index * max_results_per_page
        feed = fetch_category_page(
            category=category,
            start_date=start_date,
            end_date=end_date,
            start=start,
            max_results=max_results_per_page,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        page_total, page_candidates = parse_arxiv_feed(feed, category)
        total_results = page_total
        candidates.extend(page_candidates)
        if len(candidates) >= total_results:
            break

    if total_results is not None and total_results > len(candidates):
        print(
            "WARNING: Category may be under-collected.\n"
            f"Category: {category}\n"
            f"Collected: {len(candidates)}\n"
            f"Available: {total_results}"
        )

    return candidates


def fetch_category_page(
    category: str,
    start_date: date,
    end_date: date,
    start: int,
    max_results: int,
    sort_by: str,
    sort_order: str,
) -> bytes:
    query = quote(
        f"cat:{category} AND submittedDate:["
        f"{format_arxiv_date(start_date)} TO {format_arxiv_date(end_date, end_of_day=True)}]"
    )
    url = (
        f"{ARXIV_API_URL}?search_query={query}"
        f"&sortBy={quote(sort_by)}"
        f"&sortOrder={quote(sort_order)}"
        f"&start={start}"
        f"&max_results={max_results}"
    )
    context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(url, timeout=30, context=context) as response:
        return response.read()


def parse_arxiv_feed(feed: bytes, category: str) -> tuple[int, list[CandidatePaper]]:
    root = ET.fromstring(feed)
    total_results = int(text_of(root, "opensearch:totalResults") or 0)
    candidates = []
    for entry in root.findall("atom:entry", ATOM_NAMESPACE):
        title = text_of(entry, "atom:title")
        arxiv_url = text_of(entry, "atom:id")
        arxiv_id = arxiv_url.rsplit("/", 1)[-1] if arxiv_url else None
        authors = [
            text_of(author, "atom:name")
            for author in entry.findall("atom:author", ATOM_NAMESPACE)
        ]
        pdf_url = None
        for link in entry.findall("atom:link", ATOM_NAMESPACE):
            if link.attrib.get("title") == "pdf":
                pdf_url = link.attrib.get("href")
        candidates.append(
            CandidatePaper(
                title=normalize_whitespace(title or "Untitled arXiv Paper"),
                authors=[author for author in authors if author],
                source="arxiv",
                origin="daily_fetch",
                abstract=normalize_whitespace(text_of(entry, "atom:summary") or ""),
                arxiv_id=arxiv_id,
                url=arxiv_url,
                pdf_url=pdf_url,
                published_date=(text_of(entry, "atom:published") or "")[:10],
                category=category,
            )
        )
    return total_results, candidates


def text_of(element: ET.Element, selector: str) -> str | None:
    child = element.find(selector, ATOM_NAMESPACE)
    return child.text if child is not None else None


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def parse_arxiv_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def format_arxiv_date(value: date, end_of_day: bool = False) -> str:
    suffix = "2359" if end_of_day else "0000"
    return value.strftime(f"%Y%m%d{suffix}")
