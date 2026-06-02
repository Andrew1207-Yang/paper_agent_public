from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.common import add_workflow_args, resolve_paper_notes_dir
from src.discovery_workflow import start_my_day


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Phase 2 daily discovery workflow.")
    add_workflow_args(parser)
    parser.add_argument("--skip_triage", action="store_true")
    parser.add_argument("--max-papers", type=int)
    parser.add_argument("--max-requests", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-fallback", action="store_true")
    parser.add_argument("--retry-attempts", type=int)
    parser.add_argument("--retry-sleep-seconds", type=float)
    parser.add_argument("--top-k-for-triage", type=int)
    parser.add_argument("--skip_retrieval", action="store_true")
    args = parser.parse_args()

    vault_dir = Path(args.vault_dir).expanduser()
    result = start_my_day(
        vault_dir=vault_dir,
        paper_notes_dir=resolve_paper_notes_dir(vault_dir, args.paper_notes_dir),
        clippings_dir=Path(args.clippings_dir).expanduser(),
        resources_dir=Path(args.resources_dir).expanduser(),
        configs_dir=Path(args.configs_dir).expanduser(),
        skip_triage=args.skip_triage,
        max_papers=args.max_papers,
        max_requests=args.max_requests,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        allow_fallback=args.allow_fallback,
        max_retry_attempts=args.retry_attempts,
        retry_sleep_seconds=args.retry_sleep_seconds,
        top_k_for_triage=args.top_k_for_triage,
        skip_retrieval=args.skip_retrieval,
    )

    print(f"Clipping candidates: {result.clipping_count}")
    print(f"arXiv candidates: {result.arxiv_count}")
    print(f"Candidate notes created: {result.created_count}")
    print(f"Candidate notes updated: {result.updated_count}")
    print(f"Retrieved for triage: {result.retrieved_count}")
    print(f"Triaged candidates: {result.triaged_count}")
    print(f"Daily queue: {result.queue_path}")
    if result.arxiv_error:
        print(f"arXiv fetch warning: {result.arxiv_error}")
    print("Top candidates:")
    for title in result.top_candidates:
        print(f"- {title}")


if __name__ == "__main__":
    main()
