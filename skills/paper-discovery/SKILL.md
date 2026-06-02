# Paper Discovery

Use this skill for Phase 2 discovery and triage workflows.

Example triggers:

- start my day
- fetch papers
- refresh candidates
- update paper queue
- check new papers

Workflow:

1. Run `python scripts/start_my_day.py` with the configured vault, paper notes, and clipping directories.
2. Let semantic retrieval select top candidates before abstract triage.
3. Use `--skip_triage` for rapid iteration, or `--max-papers`, `--batch-size`, and `--max-requests` for controlled abstract triage.
4. Open the generated `Daily Queues/YYYY-MM-DD.md` note.
5. Report:
   - number of new papers
   - clipping-derived papers
   - retrieved-for-triage candidates
   - triaged candidates
   - top-ranked candidates
6. Ask which papers should be investigated further.

Do not perform deep reading, summarization, critique generation, research note writing, or preference learning.
