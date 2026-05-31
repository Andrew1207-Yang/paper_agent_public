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
    status: str
    topics: list[str]
    priority: int | None
    rating: int | None
    importance: int | None
    taste_match: int | None
    research_idea_potential: int | None
    technical_depth: int | None
    urgency: int | None
    date_added: str | None
    date_read: str | None
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
            status=status,
            topics=as_string_list(frontmatter.get("topics")),
            priority=as_score_or_none(frontmatter.get("priority")),
            rating=as_score_or_none(frontmatter.get("rating")),
            importance=as_score_or_none(frontmatter.get("importance")),
            taste_match=as_score_or_none(frontmatter.get("taste_match")),
            research_idea_potential=as_score_or_none(
                frontmatter.get("research_idea_potential")
            ),
            technical_depth=as_score_or_none(frontmatter.get("technical_depth")),
            urgency=as_score_or_none(frontmatter.get("urgency")),
            date_added=as_str_or_none(frontmatter.get("date_added")),
            date_read=as_str_or_none(frontmatter.get("date_read")),
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
            "status": self.status,
            "topics": ", ".join(self.topics),
            "priority": self.priority,
            "rating": self.rating,
            "importance": self.importance,
            "taste_match": self.taste_match,
            "research_idea_potential": self.research_idea_potential,
            "technical_depth": self.technical_depth,
            "urgency": self.urgency,
            "date_added": self.date_added,
            "date_read": self.date_read,
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
