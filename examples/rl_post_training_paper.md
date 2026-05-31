---
title: "Preference Optimization Under Sparse Feedback"
authors:
  - "Nadia Williams"
year: 2025
venue: "arXiv"
url: "https://example.com/sparse-feedback-rl"
source: "manual"
status: "skim"
topics:
  - "RL and Post-training"
  - "Learning Dynamics & Emergence"
priority: 3
rating: 3
importance: 3
taste_match: 3
research_idea_potential: 4
technical_depth: 4
urgency: 3
date_added: "2026-05-17"
date_read: null
tags:
  - paper
related_notes:
  - "[[Preference Optimization]]"
---

# Summary

Studies stability issues when preference optimization receives infrequent or delayed reward signals.

# Core Idea

The method regularizes policy updates with uncertainty estimates over sparse preference labels.

# Weaknesses

- Experiments use relatively small models.
- The reward model assumptions may not hold for open-ended tasks.

# Open Questions

- Does sparse feedback amplify reward hacking in long-horizon settings?
- Can uncertainty estimates guide active preference collection?
