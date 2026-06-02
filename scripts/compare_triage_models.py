from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.abstract_triage import format_batch
from src.llm_provider import OpenAICompatibleProvider
from src.triage_parser import parse_triage_response
from src.triage_selector import select_triage_candidates


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send one small batch through the configured model stack."
    )
    parser.add_argument("--paper_notes_dir", required=True)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-fallback", action="store_true")
    parser.add_argument("--retry-attempts", type=int)
    parser.add_argument("--retry-sleep-seconds", type=float)
    args = parser.parse_args()

    candidates = select_triage_candidates(Path(args.paper_notes_dir).expanduser())
    batch = candidates[: args.batch_size]
    print(f"Comparison batch size: {len(batch)}")
    if args.dry_run:
        for paper in format_batch(batch):
            print(f"- {paper['title']}")
        return

    provider = OpenAICompatibleProvider(
        allow_fallback=args.allow_fallback,
        max_retry_attempts=args.retry_attempts,
        retry_sleep_seconds=args.retry_sleep_seconds,
    )
    prompt = Path("prompts/abstract_triage_prompt.md").read_text(encoding="utf-8")
    response = provider.chat(prompt, json.dumps(format_batch(batch), ensure_ascii=False))
    print(f"Model: {response.model}")
    for result in parse_triage_response(response.content):
        print(result)


if __name__ == "__main__":
    main()
