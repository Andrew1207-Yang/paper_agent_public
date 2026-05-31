---
title: "Data Mixture Audits for Efficient Pretraining"
authors:
  - "Elena Rossi"
  - "Samir Gupta"
year: 2024
venue: "NeurIPS"
url: "https://example.com/data-mixture-audits"
source: "existing_notes"
status: "read"
topics:
  - "Pretraining Data"
  - "Training Pipelines"
priority: 4
rating: 5
importance: 5
taste_match: 4
research_idea_potential: 5
technical_depth: 3
urgency: 2
date_added: "2026-05-10"
date_read: "2026-05-21"
tags:
  - paper
  - data
related_notes:
  - "[[Data Curation]]"
---

# Summary

Presents lightweight audits for measuring how pretraining data mixtures affect downstream performance and memorization risk.

# Core Idea

Use smaller proxy runs to estimate which data slices contribute most to target capabilities.

# Weaknesses

- Proxy runs may not preserve scaling behavior.
- The audit metrics are useful but still indirect.

# Open Questions

- Which data-quality metrics remain predictive at frontier scale?
- Can audits identify data that improves reasoning without increasing memorization?
