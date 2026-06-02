from __future__ import annotations

import pandas as pd


def apply_filters(
    dataframe: pd.DataFrame,
    statuses: list[str],
    topics: list[str],
    sources: list[str],
    priorities: list[int],
    ratings: list[int],
    min_ranking_score: int | None = None,
    recent_only: bool = False,
    recent_days: int = 30,
    triage_decisions: list[str] | None = None,
    min_semantic_fit: int | None = None,
    min_research_potential: int | None = None,
    min_conceptual_depth: int | None = None,
    matched_interests: list[str] | None = None,
    min_semantic_score: float | None = None,
) -> pd.DataFrame:
    filtered = dataframe.copy()

    if statuses:
        filtered = filtered[filtered["status"].isin(statuses)]
    if sources:
        filtered = filtered[filtered["source"].isin(sources)]
    if priorities:
        filtered = filtered[filtered["priority"].isin(priorities)]
    if ratings:
        filtered = filtered[filtered["rating"].isin(ratings)]
    if min_ranking_score is not None:
        filtered = filtered[filtered["ranking_score"].fillna(0) >= min_ranking_score]
    if recent_only:
        published = pd.to_datetime(filtered["published_date"], errors="coerce")
        added = pd.to_datetime(filtered["date_added"], errors="coerce")
        newest_date = published.fillna(added)
        cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=recent_days)
        filtered = filtered[newest_date >= cutoff]
    if triage_decisions:
        filtered = filtered[filtered["triage_decision"].isin(triage_decisions)]
    if min_semantic_fit is not None:
        filtered = filtered[filtered["semantic_fit"].fillna(0) >= min_semantic_fit]
    if min_research_potential is not None:
        filtered = filtered[
            filtered["research_potential"].fillna(0) >= min_research_potential
        ]
    if min_conceptual_depth is not None:
        filtered = filtered[
            filtered["conceptual_depth"].fillna(0) >= min_conceptual_depth
        ]
    if matched_interests:
        filtered = filtered[filtered["matched_interest"].isin(matched_interests)]
    if min_semantic_score is not None:
        filtered = filtered[filtered["semantic_score"].fillna(0) >= min_semantic_score]
    if topics:
        filtered = filtered[
            filtered["topics"].fillna("").apply(
                lambda value: any(topic in split_topics(value) for topic in topics)
            )
        ]

    return filtered


def split_topics(value: str) -> list[str]:
    return [topic.strip() for topic in str(value).split(",") if topic.strip()]
