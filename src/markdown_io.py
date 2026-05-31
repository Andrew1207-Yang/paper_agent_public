from __future__ import annotations

from pathlib import Path
from typing import Any

from src.frontmatter import render_frontmatter, split_frontmatter


def discover_markdown_files(base_dir: Path, recursive: bool = False) -> list[Path]:
    if not base_dir.exists() or not base_dir.is_dir():
        return []

    pattern = "**/*.md" if recursive else "*.md"
    return sorted(path for path in base_dir.glob(pattern) if path.is_file())


def read_markdown_note(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    return split_frontmatter(text)


def write_markdown_note(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    path.write_text(render_frontmatter(frontmatter) + body, encoding="utf-8")
