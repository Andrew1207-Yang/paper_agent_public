from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.candidate_notes import dedupe_keys
from src.markdown_io import discover_markdown_files, read_markdown_note


def main() -> None:
    parser = argparse.ArgumentParser(description="Report duplicate candidate notes.")
    parser.add_argument("--paper_notes_dir", required=True)
    args = parser.parse_args()

    seen: dict[str, Path] = {}
    duplicates: list[tuple[Path, Path, str]] = []
    for path in discover_markdown_files(Path(args.paper_notes_dir).expanduser(), recursive=True):
        frontmatter, _ = read_markdown_note(path)
        for key in dedupe_keys(frontmatter):
            if key in seen:
                duplicates.append((seen[key], path, key))
                break
            seen[key] = path

    if not duplicates:
        print("No duplicates found.")
        return
    for first, second, key in duplicates:
        print(f"Duplicate {key}: {first} <-> {second}")


if __name__ == "__main__":
    main()
