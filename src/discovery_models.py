from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


@dataclass
class CandidatePaper:
    title: str
    authors: list[str] = field(default_factory=list)
    source: str = "manual"
    origin: str = "manual"
    abstract: str = ""
    arxiv_id: str | None = None
    url: str | None = None
    pdf_url: str | None = None
    published_date: str | None = None
    category: str | None = None
    timestamp: str | None = None
    date_added: str = field(default_factory=lambda: date.today().isoformat())
    ranking_score: int | None = None
    ranking_reason: list[str] = field(default_factory=list)
    semantic_fit: int | None = None
    importance_guess: int | None = None
    research_potential: int | None = None
    conceptual_depth: int | None = None
    triage_decision: str | None = None
    triage_confidence: int | None = None
    final_priority_score: int | None = None
    triage_model: str | None = None
    triage_date: str | None = None

    def frontmatter(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "authors": self.authors,
            "source": self.source,
            "origin": self.origin,
            "arxiv_id": self.arxiv_id,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "published_date": self.published_date,
            "category": self.category,
            "timestamp": self.timestamp,
            "status": "candidate",
            "topics": [],
            "priority": None,
            "ranking_score": self.ranking_score,
            "ranking_reason": self.ranking_reason,
            "semantic_fit": self.semantic_fit,
            "importance_guess": self.importance_guess,
            "research_potential": self.research_potential,
            "conceptual_depth": self.conceptual_depth,
            "triage_decision": self.triage_decision,
            "triage_confidence": self.triage_confidence,
            "final_priority_score": self.final_priority_score,
            "triage_model": self.triage_model,
            "triage_date": self.triage_date,
            "date_added": self.date_added,
            "already_read": False,
            "tags": ["paper", "candidate"],
        }

    @classmethod
    def from_frontmatter(cls, frontmatter: dict[str, Any], body: str = "") -> "CandidatePaper":
        return cls(
            title=str(frontmatter.get("title") or "Untitled Paper"),
            authors=as_string_list(frontmatter.get("authors")),
            source=str(frontmatter.get("source") or "manual"),
            origin=str(frontmatter.get("origin") or "manual"),
            abstract=extract_abstract_from_body(body),
            arxiv_id=as_str_or_none(frontmatter.get("arxiv_id")),
            url=as_str_or_none(frontmatter.get("url")),
            pdf_url=as_str_or_none(frontmatter.get("pdf_url")),
            published_date=as_str_or_none(frontmatter.get("published_date")),
            category=as_str_or_none(frontmatter.get("category")),
            timestamp=as_str_or_none(frontmatter.get("timestamp")),
            date_added=str(frontmatter.get("date_added") or date.today().isoformat()),
            ranking_score=as_int_or_none(frontmatter.get("ranking_score")),
            ranking_reason=as_string_list(frontmatter.get("ranking_reason")),
            semantic_fit=as_int_or_none(frontmatter.get("semantic_fit")),
            importance_guess=as_int_or_none(frontmatter.get("importance_guess")),
            research_potential=as_int_or_none(frontmatter.get("research_potential")),
            conceptual_depth=as_int_or_none(frontmatter.get("conceptual_depth")),
            triage_decision=as_str_or_none(frontmatter.get("triage_decision")),
            triage_confidence=as_int_or_none(frontmatter.get("triage_confidence")),
            final_priority_score=as_int_or_none(frontmatter.get("final_priority_score")),
            triage_model=as_str_or_none(frontmatter.get("triage_model")),
            triage_date=as_str_or_none(frontmatter.get("triage_date")),
        )


def as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None and str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value)]


def as_str_or_none(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def as_int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def extract_abstract_from_body(body: str) -> str:
    lines = body.splitlines()
    collecting = False
    abstract_lines: list[str] = []
    for line in lines:
        if line.startswith("# "):
            if collecting:
                break
            collecting = line.strip().lower() == "# abstract"
            continue
        if collecting:
            abstract_lines.append(line)
    return "\n".join(abstract_lines).strip()


def safe_note_filename(title: str) -> str:
    safe = "".join(char if char.isalnum() else "-" for char in title.lower())
    collapsed = "-".join(part for part in safe.split("-") if part)
    return f"{collapsed[:90] or 'untitled-paper'}.md"


def candidate_note_path(paper_notes_dir: Path, candidate: CandidatePaper) -> Path:
    if candidate.arxiv_id:
        return paper_notes_dir / f"arxiv-{candidate.arxiv_id.replace('/', '-')}.md"
    return paper_notes_dir / safe_note_filename(candidate.title)
