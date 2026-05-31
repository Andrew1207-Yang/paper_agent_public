from __future__ import annotations

import pandas as pd


def apply_filters(
    dataframe: pd.DataFrame,
    statuses: list[str],
    topics: list[str],
    sources: list[str],
    priorities: list[int],
    ratings: list[int],
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
    if topics:
        filtered = filtered[
            filtered["topics"].fillna("").apply(
                lambda value: any(topic in split_topics(value) for topic in topics)
            )
        ]

    return filtered


def split_topics(value: str) -> list[str]:
    return [topic.strip() for topic in str(value).split(",") if topic.strip()]
