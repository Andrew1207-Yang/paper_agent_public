---
title: "Tool-Use Traces as Agent Training Data"
authors:
  - "Priya Singh"
  - "Mateo Alvarez"
year: 2026
venue: "arXiv"
url: "https://example.com/tool-use-traces"
source: "twitter"
status: "candidate"
topics:
  - "Agents & Tool Use"
  - "Training Pipelines"
priority: 3
rating: null
importance: 3
taste_match: 3
research_idea_potential: 4
technical_depth: 2
urgency: 3
date_added: "2026-05-31"
date_read: null
tags:
  - paper
  - agents
related_notes:
  - "[[Agent Data]]"
---

# Summary

Argues that tool-use traces can be curated into training examples for more reliable task decomposition.

# Core Idea

The dataset stores tool calls, intermediate observations, and final answers as structured trajectories.

# Weaknesses

- Trace quality depends on the policy that generated the data.
- Privacy and leakage concerns are under-discussed.

# Open Questions

- What makes a tool-use trace pedagogically useful rather than merely successful?
- Can bad traces teach recovery strategies without reinforcing bad habits?
