from __future__ import annotations

from typing import Any

import yaml


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            raw_frontmatter = "".join(lines[1:index])
            body = "".join(lines[index + 1 :])
            data = yaml.safe_load(raw_frontmatter) or {}
            if not isinstance(data, dict):
                data = {}
            return data, body

    return {}, text


def render_frontmatter(data: dict[str, Any]) -> str:
    yaml_text = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    ).strip()
    return f"---\n{yaml_text}\n---\n"
