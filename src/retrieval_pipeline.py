from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.embedding_provider import EmbeddingProvider
from src.embedding_store import embeddings_by_id, upsert_embeddings
from src.markdown_io import read_markdown_note, write_markdown_note
from src.semantic_ranker import rank_by_semantic_similarity, retrieval_frontmatter
from src.taste_profile import build_taste_profile
from src.triage_selector import select_triage_candidates


@dataclass
class RetrievalPipelineResult:
    candidate_count: int
    embedded_count: int
    selected_count: int
    top_paper_ids: list[str]


def run_semantic_retrieval(
    paper_notes_dir: Path,
    top_k: int | None = None,
    dry_run: bool = False,
    settings_path: Path = Path("configs/retrieval_settings.yaml"),
    interest_queries_path: Path = Path("resources/semantic_interest_queries.yaml"),
) -> RetrievalPipelineResult:
    settings = load_yaml(settings_path)
    top_k = top_k or int(settings.get("retrieval", {}).get("top_k_for_triage", 50))
    candidates = select_triage_candidates(
        paper_notes_dir,
        require_selected_for_triage=False,
    )
    if dry_run:
        return RetrievalPipelineResult(
            candidate_count=len(candidates),
            embedded_count=0,
            selected_count=0,
            top_paper_ids=[],
        )
    provider = EmbeddingProvider(settings_path)
    paper_embeddings = ensure_paper_embeddings(candidates, provider, dry_run=dry_run)
    interest_embeddings = embed_interest_queries(interest_queries_path, provider)
    taste_profile = build_taste_profile(
        paper_notes_dir=paper_notes_dir,
        settings_path=settings_path,
    )
    ranked = rank_by_semantic_similarity(
        candidates=candidates,
        paper_embeddings=paper_embeddings,
        interest_embeddings=interest_embeddings,
        settings_path=settings_path,
        taste_embedding=taste_profile.taste_embedding,
        positive_embeddings=taste_profile.positive_embeddings,
    )
    selected_ids = {result.paper_id for result in ranked[:top_k]}
    if not dry_run:
        for result in ranked:
            update_retrieval_frontmatter(
                Path(result.paper_id),
                retrieval_frontmatter(
                    result,
                    retrieval_model=provider.model,
                    selected_for_triage=result.paper_id in selected_ids,
                ),
            )
    return RetrievalPipelineResult(
        candidate_count=len(candidates),
        embedded_count=len(paper_embeddings),
        selected_count=len(selected_ids),
        top_paper_ids=list(selected_ids),
    )


def ensure_paper_embeddings(
    candidates: list[dict[str, Any]],
    provider: EmbeddingProvider,
    dry_run: bool = False,
    debug: bool = False,
) -> dict[str, list[float]]:
    existing = embeddings_by_id()
    missing = [
        candidate for candidate in candidates if candidate["paper_id"] not in existing
    ]
    if debug:
        print(
            f"Embedding store: existing={len(existing)}, "
            f"candidates={len(candidates)}, missing={len(missing)}"
        )
    if missing and not dry_run:
        texts = [paper_embedding_text(candidate) for candidate in missing]
        embeddings = provider.embed(texts, input_type="passage", debug=debug)
        rows = [
            {
                "paper_id": candidate["paper_id"],
                "title": candidate["title"],
                "embedding": embedding,
            }
            for candidate, embedding in zip(missing, embeddings)
        ]
        upsert_embeddings(rows)
        existing = embeddings_by_id()
        if debug:
            print(f"Embedding store updated: total={len(existing)}")
    return existing


def embed_interest_queries(
    interest_queries_path: Path,
    provider: EmbeddingProvider,
) -> dict[str, list[float]]:
    queries = load_yaml(interest_queries_path).get("queries", [])
    names = [str(query.get("name")) for query in queries if query.get("text")]
    texts = [str(query.get("text")) for query in queries if query.get("text")]
    embeddings = provider.embed(texts, input_type="query")
    return dict(zip(names, embeddings))


def update_retrieval_frontmatter(path: Path, updates: dict[str, Any]) -> None:
    frontmatter, body = read_markdown_note(path)
    frontmatter.update(updates)
    write_markdown_note(path, frontmatter, body)


def paper_embedding_text(candidate: dict[str, Any]) -> str:
    return f"Title: {candidate['title']}\n\nAbstract: {candidate['abstract']}"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}
