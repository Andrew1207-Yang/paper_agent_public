from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = [
    "candidate",
    "skim",
    "read_later",
    "reading",
    "read",
    "archived",
    "ignored",
]

SCORE_VALUES = [1, 2, 3, 4, 5]

EDITABLE_FIELDS = [
    "status",
    "rating",
    "priority",
    "importance",
    "taste_match",
    "research_idea_potential",
    "technical_depth",
    "urgency",
    "topics",
    "related_notes",
    "read_status",
    "user_rating",
    "starred",
    "clipped",
]


@dataclass
class PaperNote:
    path: Path
    title: str
    authors: list[str]
    year: int | None
    venue: str | None
    url: str | None
    source: str | None
    origin: str | None
    arxiv_id: str | None
    pdf_url: str | None
    status: str
    topics: list[str]
    priority: int | None
    rating: int | None
    ranking_score: int | None
    ranking_reason: list[str]
    semantic_fit: int | None
    importance_guess: int | None
    research_potential: int | None
    conceptual_depth: int | None
    triage_decision: str | None
    triage_confidence: int | None
    final_priority_score: int | None
    triage_model: str | None
    triage_date: str | None
    semantic_score: float | None
    matched_interest: str | None
    retrieval_score: float | None
    retrieval_model: str | None
    retrieval_date: str | None
    retrieval_reason: list[str]
    nearest_positive_papers: list[str]
    selected_for_triage: bool
    read_status: str | None
    user_rating: int | None
    starred: bool
    clipped: bool
    importance: int | None
    taste_match: int | None
    research_idea_potential: int | None
    technical_depth: int | None
    urgency: int | None
    date_added: str | None
    date_read: str | None
    published_date: str | None
    already_read: bool
    tags: list[str]
    related_notes: list[str]
    body: str
    frontmatter: dict[str, Any]

    @classmethod
    def from_markdown(
        cls, path: Path, frontmatter: dict[str, Any], body: str
    ) -> "PaperNote":
        title = frontmatter.get("title") or path.stem
        status = frontmatter.get("status") or "candidate"
        if status not in ALLOWED_STATUSES:
            status = "candidate"

        return cls(
            path=path,
            title=str(title),
            authors=as_string_list(frontmatter.get("authors")),
            year=as_int_or_none(frontmatter.get("year")),
            venue=as_str_or_none(frontmatter.get("venue")),
            url=as_str_or_none(frontmatter.get("url")),
            source=as_str_or_none(frontmatter.get("source")),
            origin=as_str_or_none(frontmatter.get("origin")),
            arxiv_id=as_str_or_none(frontmatter.get("arxiv_id")),
            pdf_url=as_str_or_none(frontmatter.get("pdf_url")),
            status=status,
            topics=as_string_list(frontmatter.get("topics")),
            priority=as_score_or_none(frontmatter.get("priority")),
            rating=as_score_or_none(frontmatter.get("rating")),
            ranking_score=as_int_or_none(frontmatter.get("ranking_score")),
            ranking_reason=as_string_list(frontmatter.get("ranking_reason")),
            semantic_fit=as_score_or_none(frontmatter.get("semantic_fit")),
            importance_guess=as_score_or_none(frontmatter.get("importance_guess")),
            research_potential=as_score_or_none(frontmatter.get("research_potential")),
            conceptual_depth=as_score_or_none(frontmatter.get("conceptual_depth")),
            triage_decision=as_str_or_none(frontmatter.get("triage_decision")),
            triage_confidence=as_score_or_none(frontmatter.get("triage_confidence")),
            final_priority_score=as_int_or_none(frontmatter.get("final_priority_score")),
            triage_model=as_str_or_none(frontmatter.get("triage_model")),
            triage_date=as_str_or_none(frontmatter.get("triage_date")),
            semantic_score=as_float_or_none(frontmatter.get("semantic_score")),
            matched_interest=as_str_or_none(frontmatter.get("matched_interest")),
            retrieval_score=as_float_or_none(frontmatter.get("retrieval_score")),
            retrieval_model=as_str_or_none(frontmatter.get("retrieval_model")),
            retrieval_date=as_str_or_none(frontmatter.get("retrieval_date")),
            retrieval_reason=as_string_list(frontmatter.get("retrieval_reason")),
            nearest_positive_papers=as_string_list(
                frontmatter.get("nearest_positive_papers")
            ),
            selected_for_triage=as_bool(frontmatter.get("selected_for_triage")),
            read_status=as_str_or_none(frontmatter.get("read_status")),
            user_rating=as_score_or_none(frontmatter.get("user_rating")),
            starred=as_bool(frontmatter.get("starred")),
            clipped=as_bool(frontmatter.get("clipped")),
            importance=as_score_or_none(frontmatter.get("importance")),
            taste_match=as_score_or_none(frontmatter.get("taste_match")),
            research_idea_potential=as_score_or_none(
                frontmatter.get("research_idea_potential")
            ),
            technical_depth=as_score_or_none(frontmatter.get("technical_depth")),
            urgency=as_score_or_none(frontmatter.get("urgency")),
            date_added=as_str_or_none(frontmatter.get("date_added")),
            date_read=as_str_or_none(frontmatter.get("date_read")),
            published_date=as_str_or_none(frontmatter.get("published_date")),
            already_read=as_bool(frontmatter.get("already_read")),
            tags=as_string_list(frontmatter.get("tags")),
            related_notes=as_string_list(frontmatter.get("related_notes")),
            body=body,
            frontmatter=frontmatter,
        )

    def to_row(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "title": self.title,
            "authors": ", ".join(self.authors),
            "year": self.year,
            "venue": self.venue,
            "url": self.url,
            "source": self.source,
            "origin": self.origin,
            "arxiv_id": self.arxiv_id,
            "pdf_url": self.pdf_url,
            "status": self.status,
            "topics": ", ".join(self.topics),
            "priority": self.priority,
            "rating": self.rating,
            "ranking_score": self.ranking_score,
            "ranking_reason": "; ".join(self.ranking_reason),
            "semantic_fit": self.semantic_fit,
            "importance_guess": self.importance_guess,
            "research_potential": self.research_potential,
            "conceptual_depth": self.conceptual_depth,
            "triage_decision": self.triage_decision,
            "triage_confidence": self.triage_confidence,
            "final_priority_score": self.final_priority_score,
            "triage_model": self.triage_model,
            "triage_date": self.triage_date,
            "semantic_score": self.semantic_score,
            "matched_interest": self.matched_interest,
            "retrieval_score": self.retrieval_score,
            "retrieval_model": self.retrieval_model,
            "retrieval_date": self.retrieval_date,
            "retrieval_reason": "; ".join(self.retrieval_reason),
            "nearest_positive_papers": "; ".join(self.nearest_positive_papers),
            "selected_for_triage": self.selected_for_triage,
            "read_status": self.read_status,
            "user_rating": self.user_rating,
            "starred": self.starred,
            "clipped": self.clipped,
            "importance": self.importance,
            "taste_match": self.taste_match,
            "research_idea_potential": self.research_idea_potential,
            "technical_depth": self.technical_depth,
            "urgency": self.urgency,
            "date_added": self.date_added,
            "date_read": self.date_read,
            "published_date": self.published_date,
            "already_read": self.already_read,
        }


def as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None and str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value)]


def as_int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None


def as_float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def as_score_or_none(value: Any) -> int | None:
    number = as_int_or_none(value)
    if number in SCORE_VALUES:
        return number
    return None


def as_str_or_none(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "yes", "1"}
    return bool(value)
