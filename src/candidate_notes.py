from __future__ import annotations

from pathlib import Path

from src.discovery_models import CandidatePaper, candidate_note_path
from src.frontmatter import render_frontmatter
from src.markdown_io import discover_markdown_files, read_markdown_note, write_markdown_note


def load_existing_candidate_keys(paper_notes_dir: Path) -> dict[str, Path]:
    keys: dict[str, Path] = {}
    for path in discover_markdown_files(paper_notes_dir, recursive=True):
        frontmatter, _ = read_markdown_note(path)
        for key in dedupe_keys(frontmatter):
            keys.setdefault(key, path)
    return keys


def upsert_candidate_notes(
    paper_notes_dir: Path, candidates: list[CandidatePaper]
) -> tuple[int, int]:
    paper_notes_dir.mkdir(parents=True, exist_ok=True)
    existing_keys = load_existing_candidate_keys(paper_notes_dir)
    created = 0
    updated = 0

    for candidate in candidates:
        match_path = find_existing_candidate_path(existing_keys, candidate)
        if match_path:
            update_candidate_note(match_path, candidate)
            updated += 1
            continue

        path = candidate_note_path(paper_notes_dir, candidate)
        path.write_text(render_candidate_note(candidate), encoding="utf-8")
        created += 1
        for key in dedupe_keys(candidate.frontmatter()):
            existing_keys[key] = path

    return created, updated


def update_candidate_note(path: Path, candidate: CandidatePaper) -> None:
    frontmatter, body = read_markdown_note(path)
    for key, value in candidate.frontmatter().items():
        if value not in (None, [], ""):
            frontmatter[key] = value
    write_markdown_note(path, frontmatter, body)


def find_existing_candidate_path(
    existing_keys: dict[str, Path], candidate: CandidatePaper
) -> Path | None:
    for key in dedupe_keys(candidate.frontmatter()):
        if key in existing_keys:
            return existing_keys[key]
    return None


def dedupe_keys(frontmatter: dict) -> list[str]:
    keys = []
    arxiv_id = normalize(frontmatter.get("arxiv_id"))
    url = normalize(frontmatter.get("url"))
    title = normalize(frontmatter.get("title"))
    if arxiv_id:
        keys.append(f"arxiv:{arxiv_id}")
    if url:
        keys.append(f"url:{url}")
    if title:
        keys.append(f"title:{title}")
    return keys


def normalize(value) -> str:
    return str(value or "").strip().lower()


def render_candidate_note(candidate: CandidatePaper) -> str:
    return (
        render_frontmatter(candidate.frontmatter())
        + "\n"
        + "# Abstract\n\n"
        + (candidate.abstract or "No abstract available.")
        + "\n\n# Triage Notes\n\n"
        + "# Why It Might Matter\n\n"
        + "# Reading Decision\n"
    )
