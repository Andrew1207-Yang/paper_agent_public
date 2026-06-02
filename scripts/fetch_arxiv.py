from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.common import resolve_paper_notes_dir
from src.arxiv_client import fetch_recent_arxiv_papers
from src.candidate_notes import upsert_candidate_notes
from src.ranking import rank_candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch recent arXiv metadata.")
    parser.add_argument("--vault_dir", required=True)
    parser.add_argument("--paper_notes_dir", required=True)
    parser.add_argument("--resources_dir", default="resources")
    parser.add_argument("--configs_dir", default="configs")
    args = parser.parse_args()

    vault_dir = Path(args.vault_dir).expanduser()
    configs_dir = Path(args.configs_dir).expanduser()
    try:
        fetched = fetch_recent_arxiv_papers(configs_dir / "paper_sources.yaml")
    except Exception as error:
        print(f"arXiv fetch failed: {error}")
        return

    candidates = rank_candidates(
        fetched,
        resources_dir=Path(args.resources_dir).expanduser(),
        configs_dir=configs_dir,
    )
    created, updated = upsert_candidate_notes(
        resolve_paper_notes_dir(vault_dir, args.paper_notes_dir), candidates
    )
    print(f"arXiv papers: {len(candidates)}")
    print(f"Created: {created}")
    print(f"Updated: {updated}")


if __name__ == "__main__":
    main()
