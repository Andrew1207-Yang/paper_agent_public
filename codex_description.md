# Paper Reading System — Phase 1 Implementation Plan

## 1. Vision

The long-term goal of this project is to build a research paper management and reading system that integrates with an Obsidian knowledge base.

The final system should help:

1. Discover papers from multiple sources.
2. Rank and filter papers according to user interests.
3. Assist with paper reading and critique.
4. Generate structured Obsidian notes.
5. Track reading history and evolving research interests.
6. Surface potential research questions and open problems.
7. Build a persistent research knowledge base over time.

The system is intentionally designed in multiple phases.

This document describes **Phase 1 only**.

Phase 1 focuses on building a local dashboard and markdown infrastructure that will serve as the foundation for future agentic functionality.

No LLM integrations, crawlers, recommendation systems, or external APIs should be implemented during Phase 1.

---

# 2. Future Architecture

The intended long-term architecture is:

```text
Paper Sources
    ↓
Candidate Queue
    ↓
Ranking Layer
    ↓
Reading / Critique Agent
    ↓
Obsidian Knowledge Base
    ↓
Dashboard
    ↓
Preference Updates
```

Potential paper sources include:

* arXiv
* Semantic Scholar
* Papers With Code
* Zotero
* Manual PDF uploads
* Twitter/X research accounts
* Existing Obsidian notes

Phase 1 implements only:

```text
Obsidian Knowledge Base
    ↓
Dashboard
```

The dashboard should be designed such that future components can be integrated without major architectural changes.

---

# 3. Phase 1 Scope

## Objective

Build a local dashboard that reads markdown notes from an Obsidian vault and provides tools for:

* organizing papers
* viewing paper metadata
* tracking reading progress
* rating papers
* filtering papers
* visualizing reading activity

The dashboard should use markdown files as the source of truth.

All changes made through the UI should be written back to markdown frontmatter.

---

# 4. Explicit Non-Goals

The following should NOT be implemented in Phase 1:

## Agent Features

* Paper summarization
* Paper critique generation
* Research question generation
* Automatic note writing
* Preference learning
* Recommendation systems

## External Data Sources

* arXiv API
* Semantic Scholar API
* Papers With Code API
* Twitter/X API
* Zotero integration

## LLM Integrations

* OpenAI API
* Claude API
* Local LLMs
* Any automated reasoning agent

## Obsidian Integrations

* Obsidian plugins
* Obsidian MCP
* Local REST API integration

Phase 1 should remain a simple, stable local application.

---

# 5. Technical Requirements

## Technology Stack

Use:

```text
Python 3.10+
Streamlit
pandas
PyYAML
plotly
```

Optional:

```text
watchdog
pydantic
```

Avoid unnecessary frameworks.

---

## Project Structure

```text
paper-reading-dashboard/
├── app.py
├── requirements.txt
├── README.md
├── src/
│   ├── config.py
│   ├── markdown_io.py
│   ├── frontmatter.py
│   ├── paper_model.py
│   ├── vault_index.py
│   ├── filters.py
│   ├── update_note.py
│   └── visualizations.py
│
├── templates/
│   └── paper_note_template.md
│
├── resources/
│   ├── research_taste.md
│   ├── reading_taxonomy.md
│   ├── scoring_rubric.md
│   └── agent_design_notes.md
│
├── skills/
│   └── paper-reading/
│       └── SKILL.md
│
└── examples/
    └── sample_paper_note.md
```

---

# 6. Configuration

The Obsidian vault path must be configurable.

Required argument:

```bash
--vault_dir
```

Optional arguments:

```bash
--paper_subdir
--recursive
--debug
```

Example:

```bash
streamlit run app.py -- \
  --vault_dir "/path/to/vault" \
  --paper_subdir "Paper Notes"
```

The application should not assume any fixed directory structure inside the vault.

---

# 7. Data Model

Each paper is represented by a markdown note.

The markdown file should contain YAML frontmatter.

Example:

```markdown
---
title: "Example Paper"
authors:
  - "Author One"
year: 2025
venue: "arXiv"

url: "..."

source: "manual"

status: "candidate"

topics:
  - "Alignment"

priority: 3
rating: null

importance: 3
taste_match: 3
research_idea_potential: 3
technical_depth: 3
urgency: 3

date_added: "2026-05-31"
date_read: null

tags:
  - paper

related_notes:
  - "[[Alignment]]"
---

# Summary

# Core Idea

# Weaknesses

# Open Questions
```

Missing fields should be handled gracefully.

---

## Internal Model

Create a PaperNote object.

Minimum fields:

```python
path
title
authors
year
venue
url
source

status

topics

priority
rating

importance
taste_match
research_idea_potential
technical_depth
urgency

date_added
date_read

tags
related_notes

body
```

---

## Allowed Status Values

```text
candidate
skim
read_later
reading
read
archived
ignored
```

---

## Allowed Score Values

```text
1
2
3
4
5
```

---

# 8. Milestone 1 — Project Skeleton

## Objective

Create a working Streamlit application skeleton.

---

## Requirements

Create:

```text
app.py
requirements.txt
README.md

src/

resources/

skills/

examples/
```

Application should launch successfully.

---

## Acceptance Criteria

Running:

```bash
streamlit run app.py
```

opens a dashboard.

Dashboard displays:

```text
Paper Reading Dashboard
```

and a sidebar.

No markdown parsing is required yet.

---

# 9. Milestone 2 — Markdown Parsing

## Objective

Read markdown files from an Obsidian vault.

---

## Requirements

Implement:

* markdown file discovery
* YAML frontmatter parsing
* markdown body extraction
* safe defaults for missing fields

---

## Acceptance Criteria

Application can:

1. Find markdown files.
2. Parse frontmatter.
3. Parse body.
4. Display parsed papers.

Use sample markdown notes for testing.

---

# 10. Milestone 3 — Paper Index

## Objective

Build an in-memory index of paper notes.

---

## Requirements

Convert parsed notes into:

```python
PaperNote
```

objects.

Create a pandas DataFrame for filtering and display.

Add:

```text
Refresh Index
```

button.

---

## Acceptance Criteria

Dashboard can display:

```text
Total papers found
```

and show all indexed papers.

---

# 11. Milestone 4 — Dashboard UI

## Objective

Create the main paper management interface.

---

## Requirements

Sidebar filters:

```text
status
topic
source
priority
rating
```

Main table columns:

```text
title
topics
status
priority
rating
date_added
```

Support sorting.

---

## Acceptance Criteria

User can:

* filter papers
* sort papers
* select a paper

without editing markdown manually.

---

# 12. Milestone 5 — Paper Detail View

## Objective

Inspect and edit paper metadata.

---

## Requirements

Display:

```text
title
metadata
body
```

Allow editing:

```text
status
rating
priority

importance
taste_match
research_idea_potential
technical_depth
urgency

topics
related_notes
```

Add:

```text
Save Changes
```

button.

---

## Acceptance Criteria

Changes are written back to markdown frontmatter.

Markdown body remains unchanged.

Unknown fields are preserved.

---

# 13. Milestone 6 — Analytics

## Objective

Provide simple reading analytics.

---

## Requirements

Create:

### Overview Metrics

* Total Papers
* Read Papers
* Candidate Papers
* Average Rating

### Charts

* Papers by Status
* Papers by Topic
* Average Rating by Topic
* Papers Added Over Time

### Lists

* High Priority Unread
* Recently Added

---

## Acceptance Criteria

Dashboard updates automatically after index refresh.

---

# 14. Milestone 7 — Research Question View

## Objective

Surface manually written research ideas.

---

## Requirements

Scan markdown headings:

```text
Open Questions
Possible Research Directions
Weaknesses
```

Extract associated content.

Display:

```text
Paper Title
Question Snippet
Link to Source Note
```

---

## Acceptance Criteria

User can browse open questions across all notes from one location.

---

# 15. Required Resource Files

The following files should be created during implementation.

These are placeholders for future phases.

---

## research_taste.md

Stores user research interests.

Future agents will use this file for ranking and filtering.

---

## reading_taxonomy.md

Stores topic hierarchy.

Current categories:

```text
High Priority
- Alignment & Interpretability
- Training Pipelines
- Pretraining Data
- RL and Post-training
- Representation Learning
- Learning Dynamics & Emergence

Mid Priority
- Alternative Architectures
- Sublinear Models
- Inference Optimization
- Agents & Tool Use

Low Priority
- JEPA
- World Models
- Cognitive Science
- Neuroscience
```

---

## scoring_rubric.md

Defines meaning of scores:

```text
importance
taste_match
research_idea_potential
technical_depth
urgency
```

---

## agent_design_notes.md

Stores future plans for reading agents.

No agent implementation required.

---

## SKILL.md

Placeholder skill file for future reading workflow.

No skill implementation required.

---

# 16. Future Extensions

These are intentionally deferred.

## Phase 2

Paper ingestion:

* arXiv
* Semantic Scholar
* Papers With Code
* PDF ingestion

---

## Phase 3

Reading agent:

* summarization
* critique
* note generation
* backlink generation

---

## Phase 4

Preference system:

* rating history
* topic weighting
* evolving interests

---

## Phase 5

External integrations:

* Zotero
* Obsidian MCP
* Local REST API

---

# 17. Definition of Success

Phase 1 is complete when:

1. User can point the application to an Obsidian vault.
2. Markdown notes are indexed successfully.
3. Papers are displayed in a dashboard.
4. Papers can be filtered and sorted.
5. Paper metadata can be edited.
6. Changes are written back to markdown.
7. Reading statistics are displayed.
8. Open research questions can be browsed.
9. No external APIs or LLMs are required.
10. The codebase is clean enough to support future agentic extensions.
