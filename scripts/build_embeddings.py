from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.embedding_provider import EmbeddingProvider
from src.retrieval_pipeline import ensure_paper_embeddings
from src.triage_selector import select_triage_candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Build embeddings for candidate papers.")
    parser.add_argument("--paper_notes_dir", required=True)
    parser.add_argument("--max-papers", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    candidates = select_triage_candidates(
        Path(args.paper_notes_dir).expanduser(),
        require_selected_for_triage=False,
    )
    if args.debug:
        print(f"Selected hard-filtered candidates: {len(candidates)}")
    if args.max_papers is not None:
        candidates = candidates[: args.max_papers]
        if args.debug:
            print(f"Applied max-papers cap: {len(candidates)}")
    embeddings = ensure_paper_embeddings(
        candidates,
        EmbeddingProvider(),
        dry_run=args.dry_run,
        debug=args.debug,
    )
    print(f"Candidates: {len(candidates)}")
    print(f"Embeddings available: {len(embeddings)}")
    print(f"Dry run: {args.dry_run}")


if __name__ == "__main__":
    main()
