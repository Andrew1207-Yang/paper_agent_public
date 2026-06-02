from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from src.embedding_store import embeddings_by_id
from src.markdown_io import discover_markdown_files, read_markdown_note


TASTE_PROFILE_PATH = Path("data/taste_profile.json")
INTERACTION_HISTORY_PATH = Path("data/interaction_history.parquet")


@dataclass
class TasteProfile:
    taste_embedding: list[float] | None
    positive_embeddings: dict[str, list[float]]
    positive_count: int


def build_taste_profile(
    paper_notes_dir: Path,
    settings_path: Path = Path("configs/retrieval_settings.yaml"),
    profile_path: Path = TASTE_PROFILE_PATH,
    interaction_history_path: Path = INTERACTION_HISTORY_PATH,
) -> TasteProfile:
    settings = load_yaml(settings_path)
    taste_settings = settings.get("taste", {})
    min_examples = int(taste_settings.get("min_positive_examples", 20))
    weights = settings.get("interaction_weights", {})
    embeddings = embeddings_by_id()
    positives = collect_positive_examples(paper_notes_dir, weights)
    positive_embeddings = {
        paper_id: embeddings[paper_id]
        for paper_id, _ in positives
        if paper_id in embeddings
    }
    weighted_embeddings = [
        (embeddings[paper_id], weight)
        for paper_id, weight in positives
        if paper_id in embeddings
    ]
    taste_embedding = (
        weighted_average(weighted_embeddings)
        if len(weighted_embeddings) >= min_examples
        else None
    )
    write_taste_profile(profile_path, taste_embedding, len(weighted_embeddings))
    write_interaction_history(interaction_history_path, positives)
    return TasteProfile(
        taste_embedding=taste_embedding,
        positive_embeddings=positive_embeddings,
        positive_count=len(weighted_embeddings),
    )


def collect_positive_examples(
    paper_notes_dir: Path, weights: dict
) -> list[tuple[str, float]]:
    examples = []
    for path in discover_markdown_files(paper_notes_dir, recursive=True):
        frontmatter, _ = read_markdown_note(path)
        weight = positive_weight(frontmatter, weights)
        if weight > 0:
            examples.append((str(path), weight))
    return examples


def positive_weight(frontmatter: dict, weights: dict) -> float:
    weight = 0.0
    read_status = str(frontmatter.get("read_status") or frontmatter.get("status") or "")
    rating = frontmatter.get("user_rating", frontmatter.get("rating"))
    if read_status == "read":
        weight += float(weights.get("read", 1.0))
    if as_int(rating) == 4:
        weight += float(weights.get("rating_4", 2.0))
    if as_int(rating) == 5:
        weight += float(weights.get("rating_5", 3.0))
    if bool(frontmatter.get("starred")):
        weight += float(weights.get("starred", 2.0))
    if bool(frontmatter.get("clipped")) or frontmatter.get("source") == "clipping":
        weight += float(weights.get("clipped", 3.0))
    return weight


def weighted_average(items: list[tuple[list[float], float]]) -> list[float] | None:
    if not items:
        return None
    dimension = len(items[0][0])
    totals = [0.0] * dimension
    total_weight = 0.0
    for embedding, weight in items:
        total_weight += weight
        for index, value in enumerate(embedding):
            totals[index] += value * weight
    if not total_weight:
        return None
    return [value / total_weight for value in totals]


def write_taste_profile(path: Path, taste_embedding: list[float] | None, positive_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": date.today().isoformat(),
        "positive_count": positive_count,
        "taste_embedding_enabled": taste_embedding is not None,
        "taste_embedding": taste_embedding,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_interaction_history(path: Path, positives: list[tuple[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe = pd.DataFrame(
        [{"paper_id": paper_id, "positive_weight": weight} for paper_id, weight in positives]
    )
    dataframe.to_parquet(path, index=False)


def as_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}
