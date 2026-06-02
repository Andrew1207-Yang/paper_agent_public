from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.abstract_triage import run_abstract_triage


def main() -> None:
    parser = argparse.ArgumentParser(description="Small triage model test.")
    parser.add_argument("--paper_notes_dir", required=True)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--max-requests", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-fallback", action="store_true")
    parser.add_argument("--retry-attempts", type=int)
    parser.add_argument("--retry-sleep-seconds", type=float)
    args = parser.parse_args()

    result = run_abstract_triage(
        paper_notes_dir=Path(args.paper_notes_dir).expanduser(),
        max_papers=args.batch_size * args.max_requests,
        max_requests=args.max_requests,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        allow_fallback=args.allow_fallback,
        max_retry_attempts=args.retry_attempts,
        retry_sleep_seconds=args.retry_sleep_seconds,
    )
    print(f"Selected candidates: {result.selected_count}")
    print(f"Triaged candidates: {result.triaged_count}")


if __name__ == "__main__":
    main()
