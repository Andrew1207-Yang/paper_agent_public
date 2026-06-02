from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


PAPER_EMBEDDINGS_PATH = Path("data/paper_embeddings.parquet")


def load_embedding_store(path: Path = PAPER_EMBEDDINGS_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["paper_id", "title", "embedding"])
    dataframe = pd.read_parquet(path)
    if "embedding" in dataframe.columns:
        dataframe["embedding"] = dataframe["embedding"].apply(normalize_embedding)
    return dataframe


def save_embedding_store(dataframe: pd.DataFrame, path: Path = PAPER_EMBEDDINGS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_parquet(path, index=False)


def upsert_embeddings(rows: list[dict[str, Any]], path: Path = PAPER_EMBEDDINGS_PATH) -> None:
    if not rows:
        return
    existing = load_embedding_store(path)
    incoming = pd.DataFrame(rows)
    if existing.empty:
        save_embedding_store(incoming, path)
        return
    merged = pd.concat(
        [existing[~existing["paper_id"].isin(incoming["paper_id"])], incoming],
        ignore_index=True,
    )
    save_embedding_store(merged, path)


def embeddings_by_id(path: Path = PAPER_EMBEDDINGS_PATH) -> dict[str, list[float]]:
    dataframe = load_embedding_store(path)
    return {
        str(row["paper_id"]): normalize_embedding(row["embedding"])
        for _, row in dataframe.iterrows()
    }


def normalize_embedding(value) -> list[float]:
    if isinstance(value, list):
        return [float(item) for item in value]
    if isinstance(value, tuple):
        return [float(item) for item in value]
    if isinstance(value, str):
        return [float(item) for item in json.loads(value)]
    return list(value)
