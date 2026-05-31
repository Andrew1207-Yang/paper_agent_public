---
title: "Sublinear Attention via Learned Retrieval Slots"
authors:
  - "Kai Nakamura"
  - "Avery Stone"
year: 2023
venue: "ACL"
url: "https://example.com/retrieval-slots"
source: "manual"
status: "read_later"
topics:
  - "Sublinear Models"
  - "Inference Optimization"
priority: 2
rating: null
importance: 2
taste_match: 2
research_idea_potential: 3
technical_depth: 4
urgency: 1
date_added: "2026-04-30"
date_read: null
tags:
  - paper
  - efficiency
related_notes:
  - "[[Efficient Attention]]"
---

# Summary

Introduces learned retrieval slots that compress attention context before expensive token-token interactions.

# Core Idea

The architecture routes tokens through a small set of learned slots to reduce effective attention cost.

# Weaknesses

- The compression bottleneck may discard rare but important details.
- Benchmarks emphasize throughput more than reasoning quality.

# Possible Research Directions

- Test retrieval slots on long-context mechanistic interpretability tasks.
- Measure whether slot specialization emerges consistently across seeds.
