from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.markdown_io import discover_markdown_files, read_markdown_note
from src.paper_model import PaperNote


def index_vault(base_dir: Path, recursive: bool = False) -> list[PaperNote]:
    papers: list[PaperNote] = []
    for path in discover_markdown_files(base_dir, recursive=recursive):
        frontmatter, body = read_markdown_note(path)
        papers.append(PaperNote.from_markdown(path, frontmatter, body))
    return papers


def papers_to_dataframe(papers: list[PaperNote]) -> pd.DataFrame:
    return pd.DataFrame([paper.to_row() for paper in papers])
