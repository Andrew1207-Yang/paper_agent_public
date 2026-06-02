from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.retrieval_pipeline import run_semantic_retrieval


def main() -> None:
    parser = argparse.ArgumentParser(description="Small semantic retrieval test.")
    parser.add_argument("--paper_notes_dir", required=True)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = run_semantic_retrieval(
        paper_notes_dir=Path(args.paper_notes_dir).expanduser(),
        top_k=args.top_k,
        dry_run=args.dry_run,
    )
    print(result)


if __name__ == "__main__":
    main()
