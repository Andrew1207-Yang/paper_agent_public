from __future__ import annotations

from pathlib import Path


REQUIRED_RESOURCES = [
    "research_interest_keywords.yaml",
    "reading_taxonomy.md",
    "scoring_rubric.md",
]


def missing_required_resources(resources_dir: Path = Path("resources")) -> list[Path]:
    return [
        resources_dir / filename
        for filename in REQUIRED_RESOURCES
        if not (resources_dir / filename).exists()
    ]
