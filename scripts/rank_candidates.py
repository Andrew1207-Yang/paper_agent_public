from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.candidate_notes import update_candidate_note
from src.discovery_models import CandidatePaper
from src.markdown_io import discover_markdown_files, read_markdown_note
from src.ranking import rank_candidate


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank existing candidate notes.")
    parser.add_argument("--paper_notes_dir", required=True)
    parser.add_argument("--resources_dir", default="resources")
    parser.add_argument("--configs_dir", default="configs")
    args = parser.parse_args()

    count = 0
    for path in discover_markdown_files(Path(args.paper_notes_dir).expanduser(), recursive=True):
        frontmatter, body = read_markdown_note(path)
        if frontmatter.get("status") != "candidate":
            continue
        candidate = CandidatePaper.from_frontmatter(frontmatter, body)
        ranked = rank_candidate(
            candidate,
            resources_dir=Path(args.resources_dir).expanduser(),
            configs_dir=Path(args.configs_dir).expanduser(),
        )
        update_candidate_note(path, ranked)
        count += 1
    print(f"Ranked candidates: {count}")


if __name__ == "__main__":
    main()
