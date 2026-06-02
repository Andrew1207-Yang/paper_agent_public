You are triaging research papers from metadata only.

Question to answer:

Should this paper be read?

Use only title, authors, and abstract. Do not summarize the paper. Do not critique the paper. Do not generate research notes or research questions.

Reward:

- conceptual insight
- mechanisms
- controlled experiments
- representation learning
- learning dynamics
- emergence
- multimodal learning
- training dynamics
- data quality

Penalize:

- benchmark-only papers
- prompt engineering
- product demos
- scaling-only papers
- vague agent work
- anthropomorphic alignment claims

Be skeptical.

Return only valid JSON as an array. Return one object per input paper:

[
  {
    "paper_id": "...",
    "semantic_fit": 4,
    "importance_guess": 3,
    "research_potential": 5,
    "conceptual_depth": 4,
    "decision": "read_now",
    "triage_confidence": 4
  }
]
