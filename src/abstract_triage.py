from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

from src.llm_provider import OpenAICompatibleProvider
from src.triage_parser import parse_triage_response
from src.triage_selector import select_triage_candidates
from src.triage_update import apply_triage_result


@dataclass
class TriageRunResult:
    selected_count: int
    triaged_count: int
    skipped_count: int
    dry_run: bool


def run_abstract_triage(
    paper_notes_dir: Path,
    max_papers: int | None = None,
    max_requests: int | None = None,
    batch_size: int | None = None,
    dry_run: bool = False,
    allow_fallback: bool | None = None,
    max_retry_attempts: int | None = None,
    retry_sleep_seconds: float | None = None,
    settings_path: Path = Path("configs/triage_settings.yaml"),
    model_path: Path = Path("configs/triage_model.yaml"),
    prompt_path: Path = Path("prompts/abstract_triage_prompt.md"),
) -> TriageRunResult:
    settings = load_yaml(settings_path)
    if not settings.get("enabled", True):
        return TriageRunResult(0, 0, 0, dry_run)

    budget = settings.get("budget", {})
    batching = settings.get("batching", {})
    batch_size = batch_size or int(budget.get("batch_size", 40))
    max_requests = max_requests or int(budget.get("max_requests_per_day", 40))
    max_candidates = max_papers or int(budget.get("max_candidates_per_day", 1600))
    capacity = batch_size * max_requests
    candidates = select_triage_candidates(paper_notes_dir, settings_path=settings_path)
    original_count = len(candidates)
    if original_count > capacity:
        print(
            "WARNING: Candidate count exceeds daily triage budget.\n"
            f"Candidates: {original_count}\n"
            f"Capacity: {capacity}\n"
            f"Skipped: {original_count - capacity}"
        )
    if original_count > max_candidates:
        print(
            "WARNING: Candidate count exceeds configured max candidates per day.\n"
            f"Candidates: {original_count}\n"
            f"Max candidates: {max_candidates}\n"
            f"Skipped: {original_count - max_candidates}"
        )
        candidates = candidates[:max_candidates]

    if len(candidates) > capacity:
        skipped = max(original_count - capacity, len(candidates) - capacity)
        candidates = candidates[:capacity]
    else:
        skipped = max(0, original_count - len(candidates))

    provider = (
        None
        if dry_run
        else OpenAICompatibleProvider(
            model_path,
            allow_fallback=allow_fallback,
            max_retry_attempts=max_retry_attempts,
            retry_sleep_seconds=retry_sleep_seconds,
        )
    )
    prompt = prompt_path.read_text(encoding="utf-8")
    triaged_count = 0

    for request_index, batch in enumerate(chunked(candidates, batch_size)):
        if request_index >= max_requests:
            break
        if request_index > 0:
            time.sleep(float(batching.get("sleep_seconds_between_batches", 2)))
        if dry_run:
            triaged_count += len(batch)
            continue

        user_payload = json.dumps(format_batch(batch), ensure_ascii=False, indent=2)
        print(f"Sending request index: {request_index+1}/{len(candidates)// batch_size}")
        response = provider.chat(prompt, user_payload)
        print(response.content)
        results = parse_triage_response(response.content)
        results_by_id = {result["paper_id"]: result for result in results}
        for candidate in batch:
            result = results_by_id.get(candidate["paper_id"])
            if not result:
                continue
            apply_triage_result(candidate["path"], result, response.model, dry_run=dry_run)
            triaged_count += 1

    return TriageRunResult(
        selected_count=len(candidates),
        triaged_count=triaged_count,
        skipped_count=skipped,
        dry_run=dry_run,
    )


def format_batch(candidates: list[dict]) -> list[dict]:
    return [
        {
            "paper_id": candidate["paper_id"],
            "title": candidate["title"],
            "authors": candidate["authors"],
            "abstract": candidate["abstract"],
        }
        for candidate in candidates
    ]


def chunked(items: list[dict], size: int) -> list[list[dict]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}
