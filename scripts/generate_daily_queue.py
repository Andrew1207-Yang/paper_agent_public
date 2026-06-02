from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.common import resolve_paper_notes_dir
from src.daily_queue import generate_daily_queue
from src.discovery_models import CandidatePaper
from src.markdown_io import discover_markdown_files, read_markdown_note
from src.ranking import rank_candidate


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a daily queue from candidate notes.")
    parser.add_argument("--vault_dir", required=True)
    parser.add_argument("--paper_notes_dir", required=True)
    parser.add_argument("--resources_dir", default="resources")
    parser.add_argument("--configs_dir", default="configs")
    args = parser.parse_args()

    vault_dir = Path(args.vault_dir).expanduser()
    paper_notes_dir = resolve_paper_notes_dir(vault_dir, args.paper_notes_dir)
    candidates = []
    for path in discover_markdown_files(paper_notes_dir, recursive=True):
        frontmatter, body = read_markdown_note(path)
        if frontmatter.get("status") != "candidate":
            continue
        candidates.append(
            rank_candidate(
                CandidatePaper.from_frontmatter(frontmatter, body),
                resources_dir=Path(args.resources_dir).expanduser(),
                configs_dir=Path(args.configs_dir).expanduser(),
            )
        )
    queue_path = generate_daily_queue(vault_dir, candidates)
    print(f"Daily queue: {queue_path}")


if __name__ == "__main__":
    main()
