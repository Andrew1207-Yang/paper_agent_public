from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.arxiv_client import fetch_recent_arxiv_papers
from src.candidate_notes import upsert_candidate_notes
from src.clippings import ingest_clippings
from src.daily_queue import generate_daily_queue
from src.discovery_models import CandidatePaper
from src.markdown_io import discover_markdown_files, read_markdown_note
from src.ranking import rank_candidates
from src.abstract_triage import run_abstract_triage
from src.retrieval_pipeline import run_semantic_retrieval


@dataclass
class WorkflowResult:
    clipping_count: int
    arxiv_count: int
    created_count: int
    updated_count: int
    queue_path: Path
    top_candidates: list[str]
    arxiv_error: str | None = None
    triaged_count: int = 0
    retrieved_count: int = 0


def start_my_day(
    vault_dir: Path,
    paper_notes_dir: Path,
    clippings_dir: Path,
    resources_dir: Path = Path("resources"),
    configs_dir: Path = Path("configs"),
    skip_triage: bool = False,
    max_papers: int | None = None,
    max_requests: int | None = None,
    batch_size: int | None = None,
    dry_run: bool = False,
    allow_fallback: bool | None = None,
    max_retry_attempts: int | None = None,
    retry_sleep_seconds: float | None = None,
    top_k_for_triage: int | None = None,
    skip_retrieval: bool = False,
) -> WorkflowResult:
    clipping_candidates = ingest_clippings(clippings_dir)
    arxiv_error = None
    try:
        arxiv_candidates = fetch_recent_arxiv_papers(configs_dir / "paper_sources.yaml")
    except Exception as error:
        arxiv_candidates = []
        arxiv_error = str(error)
    ranked = rank_candidates(
        clipping_candidates + arxiv_candidates,
        resources_dir=resources_dir,
        configs_dir=configs_dir,
    )
    created, updated = upsert_candidate_notes(paper_notes_dir, ranked)
    retrieved_count = 0
    if not skip_retrieval:
        retrieval_result = run_semantic_retrieval(
            paper_notes_dir=paper_notes_dir,
            top_k=top_k_for_triage,
            dry_run=dry_run,
        )
        retrieved_count = retrieval_result.selected_count
    triaged_count = 0
    if not skip_triage:
        triage_result = run_abstract_triage(
            paper_notes_dir=paper_notes_dir,
            max_papers=max_papers,
            max_requests=max_requests,
            batch_size=batch_size,
            dry_run=dry_run,
            allow_fallback=allow_fallback,
            max_retry_attempts=max_retry_attempts,
            retry_sleep_seconds=retry_sleep_seconds,
        )
        triaged_count = triage_result.triaged_count
    queue_candidates = load_queue_candidates(paper_notes_dir)
    queue_path = generate_daily_queue(vault_dir, queue_candidates)
    return WorkflowResult(
        clipping_count=len(clipping_candidates),
        arxiv_count=len(arxiv_candidates),
        created_count=created,
        updated_count=updated,
        queue_path=queue_path,
        top_candidates=[candidate.title for candidate in queue_candidates[:5]],
        arxiv_error=arxiv_error,
        triaged_count=triaged_count,
        retrieved_count=retrieved_count,
    )


def load_queue_candidates(paper_notes_dir: Path) -> list[CandidatePaper]:
    candidates = []
    for path in discover_markdown_files(paper_notes_dir, recursive=True):
        frontmatter, body = read_markdown_note(path)
        if frontmatter.get("status") != "candidate":
            continue
        candidates.append(CandidatePaper.from_frontmatter(frontmatter, body))
    return sorted(
        candidates,
        key=lambda candidate: candidate.final_priority_score
        or candidate.ranking_score
        or 0,
        reverse=True,
    )
