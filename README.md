# Paper Reading Dashboard

Local Streamlit dashboard for managing research paper notes in an Obsidian vault.

Phase 1 is intentionally simple: markdown files are the source of truth, and the UI reads from and writes to YAML frontmatter. There are no external APIs, LLM integrations, crawlers, or Obsidian plugins.

## Install

```bash
uv sync
```

## Run

```bash
uv run streamlit run app.py -- \
  --vault_dir "/path/to/vault" \
  --paper_subdir "Paper Notes" \
  --recursive
```

Only `--vault_dir` is required. `--paper_subdir`, `--recursive`, and `--debug` are optional.

You can also launch with no arguments and enter the vault path in the sidebar:

```bash
uv run streamlit run app.py
```

## Phase 2 Daily Discovery

Phase 2 adds deterministic paper discovery and triage. It ingests user clipping files, fetches recent arXiv metadata, writes candidate notes into the vault, ranks them with transparent heuristics, and generates a daily queue note.

```bash
uv run python scripts/start_my_day.py \
  --vault_dir "/path/to/vault" \
  --paper_notes_dir "Paper Inbox" \
  --clippings_dir "/path/to/research/clippings"
```

Configuration lives in:

- `configs/paper_sources.yaml`
- `configs/ranking_rules.yaml`
- `configs/author_watchlist.yaml`
- `resources/research_interest_keywords.yaml`

Phase 2 does not use LLMs, summaries, critiques, PDF reading, or preference learning.

## Phase 2.5 Abstract Triage

Phase 2.5 improves arXiv coverage with date-windowed category queries and optional batched abstract triage. Triage only answers whether a paper looks worth reading from title/authors/abstract. It does not summarize, critique, read PDFs, or generate notes.

Copy the environment template and add keys as needed:

```bash
cp .env.example .env
```

Run a cheap dry-run first:

```bash
uv run python scripts/semantic_retrieval.py \
  --paper_notes_dir "/path/to/vault/Paper Inbox" \
  --top-k 50

uv run python scripts/abstract_triage.py \
  --paper_notes_dir "/path/to/vault/Paper Inbox" \
  --max-papers 20 \
  --batch-size 5 \
  --max-requests 4 \
  --dry-run
```

By default, triage retries the primary model and does not use fallback models. To opt into fallbacks:

```bash
uv run python scripts/abstract_triage.py \
  --paper_notes_dir "/path/to/vault/Paper Inbox" \
  --max-papers 20 \
  --batch-size 5 \
  --max-requests 4 \
  --retry-attempts 3 \
  --retry-sleep-seconds 10 \
  --allow-fallback
```

Run the full daily workflow without triage:

```bash
uv run python scripts/start_my_day.py \
  --vault_dir "/path/to/vault" \
  --paper_notes_dir "Paper Inbox" \
  --clippings_dir "/path/to/research/clippings" \
  --skip_triage
```

Run the daily workflow with limited triage:

```bash
uv run python scripts/start_my_day.py \
  --vault_dir "/path/to/vault" \
  --paper_notes_dir "Paper Inbox" \
  --clippings_dir "/path/to/research/clippings" \
  --max-papers 100 \
  --batch-size 10 \
  --max-requests 10
```

## Phase 2.7 Semantic Retrieval

Semantic retrieval reduces a large candidate set to the most relevant candidates before abstract triage.

```bash
uv run python scripts/semantic_retrieval.py \
  --paper_notes_dir "/path/to/vault/Paper Inbox" \
  --top-k 50
```

Configuration lives in:

- `configs/retrieval_settings.yaml`
- `resources/semantic_interest_queries.yaml`

Generated embedding/taste files live under `data/` and are ignored by git.

## Phase 2.8 Taste-Aware Retrieval

Taste-aware retrieval uses only explicit user actions:

- `read_status: read`
- `user_rating: 4` or `user_rating: 5`
- `starred: true`
- `clipped: true`

Before 20 positive examples, retrieval relies on stated semantic interests. After 20 positives with embeddings, the taste embedding is blended into retrieval scoring.

## Markdown Format

Each paper is a markdown note with YAML frontmatter. Unknown frontmatter fields are preserved when the dashboard updates editable metadata.

See `examples/sample_paper_note.md` and `templates/paper_note_template.md`.
