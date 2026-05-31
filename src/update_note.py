from __future__ import annotations

from pathlib import Path
from typing import Any

from src.markdown_io import read_markdown_note, write_markdown_note
from src.paper_model import EDITABLE_FIELDS


def update_note_frontmatter(path: Path, updates: dict[str, Any]) -> None:
    frontmatter, body = read_markdown_note(path)
    for field in EDITABLE_FIELDS:
        if field in updates:
            frontmatter[field] = updates[field]
    write_markdown_note(path, frontmatter, body)
