from __future__ import annotations

import pandas as pd
import plotly.express as px

from src.filters import split_topics


def papers_by_status(dataframe: pd.DataFrame):
    counts = dataframe["status"].fillna("unknown").value_counts().reset_index()
    counts.columns = ["status", "count"]
    return px.bar(counts, x="status", y="count", title="Papers by Status")


def papers_by_topic(dataframe: pd.DataFrame):
    topics = explode_topics(dataframe)
    counts = topics["topic"].value_counts().reset_index()
    counts.columns = ["topic", "count"]
    return px.bar(counts, x="topic", y="count", title="Papers by Topic")


def average_rating_by_topic(dataframe: pd.DataFrame):
    topics = explode_topics(dataframe)
    topics = topics.dropna(subset=["rating"])
    if topics.empty:
        return None
    grouped = topics.groupby("topic", as_index=False)["rating"].mean()
    return px.bar(grouped, x="topic", y="rating", title="Average Rating by Topic")


def papers_added_over_time(dataframe: pd.DataFrame):
    dated = dataframe.copy()
    dated["date_added"] = pd.to_datetime(dated["date_added"], errors="coerce")
    dated = dated.dropna(subset=["date_added"])
    if dated.empty:
        return None
    counts = dated.groupby(dated["date_added"].dt.date).size().reset_index(name="count")
    return px.line(counts, x="date_added", y="count", title="Papers Added Over Time")


def explode_topics(dataframe: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dataframe.iterrows():
        for topic in split_topics(row.get("topics", "")):
            rows.append({"topic": topic, "rating": row.get("rating")})
    return pd.DataFrame(rows, columns=["topic", "rating"])
