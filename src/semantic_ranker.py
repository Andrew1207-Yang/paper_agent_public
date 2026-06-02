from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RetrievalResult:
    paper_id: str
    semantic_score: float
    matched_interest: str | None
    retrieval_score: float
    retrieval_reason: list[str] = field(default_factory=list)
    nearest_positive_papers: list[str] = field(default_factory=list)


def rank_by_semantic_similarity(
    candidates: list[dict[str, Any]],
    paper_embeddings: dict[str, list[float]],
    interest_embeddings: dict[str, list[float]],
    settings_path: Path = Path("configs/retrieval_settings.yaml"),
    taste_embedding: list[float] | None = None,
    positive_embeddings: dict[str, list[float]] | None = None,
) -> list[RetrievalResult]:
    settings = load_yaml(settings_path)
    category_weights = settings.get("category_weights", {})
    author_weight = float(settings.get("author_boost", {}).get("weight", 0.05))
    author_boost_enabled = bool(settings.get("author_boost", {}).get("enabled", True))
    taste_settings = settings.get("taste", {})
    taste_enabled = taste_embedding is not None and bool(taste_settings.get("enabled", True))
    interest_weight = float(taste_settings.get("interest_weight", 0.4)) if taste_enabled else 1.0
    taste_weight = float(taste_settings.get("taste_weight", 0.6)) if taste_enabled else 0.0
    nearest_count = int(taste_settings.get("nearest_positive_count", 3))

    results = []
    for candidate in candidates:
        paper_id = candidate["paper_id"]
        embedding = paper_embeddings.get(paper_id)
        if not embedding:
            continue
        matched_interest, interest_similarity = best_interest_match(
            embedding, interest_embeddings
        )
        taste_similarity = cosine_similarity(embedding, taste_embedding) if taste_enabled else 0.0
        semantic_score = interest_weight * interest_similarity + taste_weight * taste_similarity
        category_weight = float(category_weights.get(candidate.get("category"), 1.0))
        author_boost = author_weight if author_boost_enabled and candidate.get("watchlist_author") else 0.0
        clipping_boost = 0.03 if candidate.get("source") == "clipping" else 0.0
        retrieval_score = semantic_score * category_weight + author_boost + clipping_boost
        reasons = []
        if matched_interest:
            reasons.append(f"matched_interest: {matched_interest}")
        if taste_enabled:
            reasons.append("taste_similarity: enabled")
        if author_boost:
            reasons.append("watchlist_author: true")
        if category_weight != 1.0:
            reasons.append(f"category_weight: {candidate.get('category')}={category_weight}")
        if clipping_boost:
            reasons.append("clipping_prior: true")
        nearest = nearest_positive_papers(
            embedding, positive_embeddings or {}, nearest_count
        ) if taste_enabled else []
        for paper in nearest:
            reasons.append(f"similar_to: {paper}")
        results.append(
            RetrievalResult(
                paper_id=paper_id,
                semantic_score=semantic_score,
                matched_interest=matched_interest,
                retrieval_score=retrieval_score,
                retrieval_reason=reasons,
                nearest_positive_papers=nearest,
            )
        )

    return sorted(results, key=lambda result: result.retrieval_score, reverse=True)


def best_interest_match(
    embedding: list[float], interest_embeddings: dict[str, list[float]]
) -> tuple[str | None, float]:
    best_name = None
    best_score = -1.0
    for name, interest_embedding in interest_embeddings.items():
        score = cosine_similarity(embedding, interest_embedding)
        if score > best_score:
            best_name = name
            best_score = score
    return best_name, best_score


def nearest_positive_papers(
    embedding: list[float],
    positive_embeddings: dict[str, list[float]],
    count: int,
) -> list[str]:
    scored = [
        (paper_id, cosine_similarity(embedding, positive_embedding))
        for paper_id, positive_embedding in positive_embeddings.items()
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    return [paper_id for paper_id, _ in scored[:count]]


def cosine_similarity(left: list[float], right: list[float] | None) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sum(a * a for a in left) ** 0.5
    right_norm = sum(b * b for b in right) ** 0.5
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def retrieval_frontmatter(
    result: RetrievalResult,
    retrieval_model: str,
    selected_for_triage: bool,
) -> dict[str, Any]:
    return {
        "semantic_score": round(result.semantic_score, 6),
        "matched_interest": result.matched_interest,
        "retrieval_score": round(result.retrieval_score, 6),
        "retrieval_model": retrieval_model,
        "retrieval_date": date.today().isoformat(),
        "retrieval_reason": result.retrieval_reason,
        "nearest_positive_papers": result.nearest_positive_papers,
        "selected_for_triage": selected_for_triage,
    }


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}
