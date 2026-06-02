from __future__ import annotations

from pathlib import Path

import yaml

from src.candidate_notes import dedupe_keys
from src.discovery_models import extract_abstract_from_body
from src.markdown_io import discover_markdown_files, read_markdown_note


SKIP_STATUSES = {"archived", "ignored", "read"}


def select_triage_candidates(
    paper_notes_dir: Path,
    settings_path: Path = Path("configs/triage_settings.yaml"),
    require_selected_for_triage: bool | None = None,
) -> list[dict]:
    settings = load_yaml(settings_path)
    behavior = settings.get("behavior", {})
    overwrite = bool(behavior.get("overwrite_existing_triage", False))
    require_abstract = bool(behavior.get("require_abstract", True))
    skip_missing_abstract = bool(behavior.get("skip_if_missing_abstract", True))
    selected_only = (
        settings.get("selection", {}).get("mode") == "semantic_retrieval_top_k"
        if require_selected_for_triage is None
        else require_selected_for_triage
    )

    candidates = []
    seen_keys: set[str] = set()
    for path in discover_markdown_files(paper_notes_dir, recursive=True):
        frontmatter, body = read_markdown_note(path)
        status = str(frontmatter.get("status") or "").lower()
        abstract = extract_abstract_from_body(body)
        title = str(frontmatter.get("title") or path.stem)

        if status in SKIP_STATUSES:
            continue
        if str(frontmatter.get("read_status") or "").lower() == "read":
            continue
        if frontmatter.get("already_read") is True:
            continue
        if not overwrite and frontmatter.get("triage_decision"):
            continue
        if "withdrawn" in title.lower() or "withdrawn" in abstract.lower():
            continue
        if require_abstract and skip_missing_abstract and not abstract:
            continue
        if selected_only and frontmatter.get("selected_for_triage") is not True:
            continue
        keys = dedupe_keys(frontmatter)
        if any(key in seen_keys for key in keys):
            continue
        seen_keys.update(keys)

        candidates.append(
            {
                "paper_id": str(path),
                "path": path,
                "title": title,
                "authors": frontmatter.get("authors") or [],
                "abstract": abstract,
                "ranking_score": frontmatter.get("ranking_score") or 0,
                "source": frontmatter.get("source") or "manual",
                "category": frontmatter.get("category"),
                "watchlist_author": has_watchlist_author(frontmatter),
            }
        )
    return candidates


def has_watchlist_author(frontmatter: dict) -> bool:
    watchlist = load_yaml(Path("configs/author_watchlist.yaml")).get("authors", [])
    authors = {str(author).lower() for author in frontmatter.get("authors") or []}
    watched = {str(author).lower() for author in watchlist}
    return bool(authors.intersection(watched))


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}
