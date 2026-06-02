from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path

from src.discovery_models import CandidatePaper


def generate_daily_queue(
    vault_dir: Path,
    candidates: list[CandidatePaper],
    queue_date: date | None = None,
) -> Path:
    queue_date = queue_date or date.today()
    queue_dir = vault_dir / "Daily Queues"
    queue_dir.mkdir(parents=True, exist_ok=True)
    path = queue_dir / f"{queue_date.isoformat()}.md"
    path.write_text(render_daily_queue(candidates), encoding="utf-8")
    return path


def render_daily_queue(candidates: list[CandidatePaper]) -> str:
    groups = group_candidates(candidates)
    sections = [
        "# Daily Paper Queue",
        "",
        "## User Clippings",
        render_candidate_lines(groups["User Clippings"]),
        "",
        "---",
        "",
        "## High Priority Candidates",
        render_candidate_lines(groups["High Priority Candidates"]),
        "",
        "---",
        "",
        "## Medium Priority",
        render_candidate_lines(groups["Medium Priority"]),
        "",
        "---",
        "",
        "## Low Priority",
        render_candidate_lines(groups["Low Priority"]),
        "",
    ]
    return "\n".join(sections)


def group_candidates(candidates: list[CandidatePaper]) -> dict[str, list[CandidatePaper]]:
    groups: dict[str, list[CandidatePaper]] = defaultdict(list)
    for candidate in sorted(candidates, key=candidate_sort_key, reverse=True):
        if candidate.source == "clipping":
            groups["User Clippings"].append(candidate)
        elif display_score(candidate) >= 14 or candidate.triage_decision == "read_now":
            groups["High Priority Candidates"].append(candidate)
        elif display_score(candidate) >= 7:
            groups["Medium Priority"].append(candidate)
        else:
            groups["Low Priority"].append(candidate)
    return groups


def render_candidate_lines(candidates: list[CandidatePaper]) -> str:
    if not candidates:
        return "_No papers in this section._"
    lines = []
    for candidate in candidates:
        score = display_score(candidate)
        decision = candidate.triage_decision or "untriaged"
        lines.append(
            f"- {candidate.title} — score: {score} — "
            f"decision: {decision} — source: {candidate.source}"
        )
    return "\n".join(lines)


def display_score(candidate: CandidatePaper) -> int:
    return candidate.final_priority_score or candidate.ranking_score or 0


def candidate_sort_key(candidate: CandidatePaper) -> tuple[int, int, int]:
    decision_order = {"read_now": 4, "skim": 3, "read_later": 2, "skip": 1}
    source_order = {"clipping": 2}
    return (
        decision_order.get(candidate.triage_decision or "", 0),
        source_order.get(candidate.source, 0),
        display_score(candidate),
    )
