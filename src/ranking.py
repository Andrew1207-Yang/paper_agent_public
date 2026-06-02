from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from src.discovery_models import CandidatePaper


DEFAULT_RANKING_RULES = {
    "source_scores": {
        "clipping": 5,
        "manual_pdf": 4,
        "arxiv": 2,
        "manual": 2,
    },
    "topic_match_scores": {
        "high_priority": 3,
        "medium_priority": 2,
        "low_priority": 1,
    },
    "author_watchlist_score": 3,
    "recency_scores": {
        "within_7_days": 2,
        "within_30_days": 1,
    },
}


def rank_candidate(
    candidate: CandidatePaper,
    resources_dir: Path = Path("resources"),
    configs_dir: Path = Path("configs"),
) -> CandidatePaper:
    rules = load_yaml(configs_dir / "ranking_rules.yaml", DEFAULT_RANKING_RULES)
    interests = load_yaml(resources_dir / "research_interest_keywords.yaml", {})
    watchlist = load_yaml(configs_dir / "author_watchlist.yaml", {})

    score = 0
    reasons: list[str] = []

    source_score = int(rules.get("source_scores", {}).get(candidate.source, 0))
    if source_score:
        score += source_score
        reasons.append(f"{candidate.source} source +{source_score}")

    topic_score, topic_reasons = score_keyword_matches(candidate, interests, rules)
    score += topic_score
    reasons.extend(topic_reasons)

    author_score, author_reasons = score_watchlist_authors(candidate, watchlist, rules)
    score += author_score
    reasons.extend(author_reasons)

    recency_score, recency_reason = score_recency(candidate, rules)
    score += recency_score
    if recency_reason:
        reasons.append(recency_reason)

    candidate.ranking_score = score
    candidate.ranking_reason = reasons or ["No ranking signals matched"]
    return candidate


def rank_candidates(
    candidates: list[CandidatePaper],
    resources_dir: Path = Path("resources"),
    configs_dir: Path = Path("configs"),
) -> list[CandidatePaper]:
    ranked = [
        rank_candidate(candidate, resources_dir=resources_dir, configs_dir=configs_dir)
        for candidate in candidates
    ]
    return sorted(ranked, key=lambda candidate: candidate.ranking_score or 0, reverse=True)


def score_keyword_matches(
    candidate: CandidatePaper, interests: dict[str, Any], rules: dict[str, Any]
) -> tuple[int, list[str]]:
    searchable = f"{candidate.title}\n{candidate.abstract}\n{candidate.category or ''}".lower()
    weights = rules.get("topic_match_scores", {})
    score = 0
    reasons: list[str] = []

    for priority_name, keywords in interests.items():
        priority_score = int(weights.get(priority_name, 0))
        for keyword in keywords or []:
            if str(keyword).lower() in searchable:
                score += priority_score
                reasons.append(f"Matched {priority_name} keyword: {keyword}")

    return score, reasons


def score_watchlist_authors(
    candidate: CandidatePaper, watchlist: dict[str, Any], rules: dict[str, Any]
) -> tuple[int, list[str]]:
    authors = {author.lower() for author in candidate.authors}
    watched_authors = {
        str(author).lower()
        for author in watchlist.get("authors", [])
        if str(author).strip()
    }
    score_per_author = int(rules.get("author_watchlist_score", 0))
    matched = sorted(authors.intersection(watched_authors))
    return (
        score_per_author * len(matched),
        [f"Author on watchlist: {author}" for author in matched],
    )


def score_recency(
    candidate: CandidatePaper, rules: dict[str, Any]
) -> tuple[int, str | None]:
    published = parse_date(candidate.published_date or candidate.date_added)
    if not published:
        return 0, None

    days_old = (date.today() - published).days
    recency_scores = rules.get("recency_scores", {})
    if days_old < 7:
        score = int(recency_scores.get("within_7_days", 0))
        return score, f"Published within 7 days +{score}"
    if days_old < 30:
        score = int(recency_scores.get("within_30_days", 0))
        return score, f"Published within 30 days +{score}"
    return 0, None


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for date_format in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    return None


def load_yaml(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else default
