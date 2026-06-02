from __future__ import annotations

from datetime import date
from pathlib import Path

from src.markdown_io import read_markdown_note, write_markdown_note


def apply_triage_result(path: Path, result: dict, model: str, dry_run: bool = False) -> dict:
    frontmatter, body = read_markdown_note(path)
    ranking_score = int(frontmatter.get("ranking_score") or 0)
    final_priority_score = (
        ranking_score
        + int(result["semantic_fit"])
        + int(result["research_potential"])
        + int(result["conceptual_depth"])
    )
    priority = priority_from_final_score(final_priority_score)
    updates = {
        "semantic_fit": result["semantic_fit"],
        "importance_guess": result["importance_guess"],
        "research_potential": result["research_potential"],
        "conceptual_depth": result["conceptual_depth"],
        "triage_decision": result["triage_decision"],
        "triage_confidence": result["triage_confidence"],
        "final_priority_score": final_priority_score,
        "priority": priority,
        "triage_model": model,
        "triage_date": date.today().isoformat(),
    }
    frontmatter.update(updates)
    if not dry_run:
        write_markdown_note(path, frontmatter, body)
    return updates


def priority_from_final_score(score: int) -> int:
    if score >= 18:
        return 5
    if score >= 14:
        return 4
    if score >= 10:
        return 3
    if score >= 7:
        return 2
    return 1
