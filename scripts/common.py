from __future__ import annotations

import argparse
from pathlib import Path


def add_workflow_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--vault_dir", required=True)
    parser.add_argument("--paper_notes_dir", required=True)
    parser.add_argument("--clippings_dir", required=True)
    parser.add_argument("--resources_dir", default="resources")
    parser.add_argument("--configs_dir", default="configs")


def resolve_paper_notes_dir(vault_dir: Path, paper_notes_dir: str) -> Path:
    path = Path(paper_notes_dir).expanduser()
    if path.is_absolute():
        return path
    return vault_dir / paper_notes_dir
