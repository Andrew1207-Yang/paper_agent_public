from __future__ import annotations

import json
import re
from typing import Any


VALID_DECISIONS = {"read_now", "skim", "read_later", "skip"}


def parse_triage_response(text: str) -> list[dict[str, Any]]:
    data = json.loads(extract_json_array(text))
    if not isinstance(data, list):
        raise ValueError("Triage response must be a JSON array")
    return [normalize_entry(entry) for entry in data if isinstance(entry, dict)]


def extract_json_array(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        return stripped
    match = re.search(r"\[.*\]", stripped, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in triage response")
    return match.group(0)


def normalize_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "paper_id": str(entry.get("paper_id") or ""),
        "semantic_fit": clamp_score(entry.get("semantic_fit")),
        "importance_guess": clamp_score(entry.get("importance_guess")),
        "research_potential": clamp_score(entry.get("research_potential")),
        "conceptual_depth": clamp_score(entry.get("conceptual_depth")),
        "triage_decision": normalize_decision(entry.get("decision")),
        "triage_confidence": clamp_score(entry.get("triage_confidence"), default=3),
    }


def clamp_score(value, default: int = 1) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        score = default
    return min(5, max(1, score))


def normalize_decision(value) -> str:
    decision = str(value or "read_later")
    return decision if decision in VALID_DECISIONS else "read_later"
