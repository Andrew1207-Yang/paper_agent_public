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

## Markdown Format

Each paper is a markdown note with YAML frontmatter. Unknown frontmatter fields are preserved when the dashboard updates editable metadata.

See `examples/sample_paper_note.md` and `templates/paper_note_template.md`.
