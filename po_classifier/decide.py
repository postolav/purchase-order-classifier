"""Merge rule + LLM scores, apply thresholds, and gate the review queue."""

from __future__ import annotations

from typing import Dict, List

from .models import Decision, PORow, Score


def decide(
    rows: List[PORow],
    rule_scores: List[Score],
    llm_scores: Dict[int, Score],
    keep_threshold: float,
    review_threshold: float,
) -> List[Decision]:
    decisions: List[Decision] = []
    for row, rs in zip(rows, rule_scores):
        # Stage 2 overrides Stage 1 wherever it ran.
        score = llm_scores.get(row.row_index, rs)
        decision = "keep" if score.similarity >= keep_threshold else "discard"
        needs_review = score.confidence < review_threshold
        decisions.append(
            Decision(row=row, score=score, decision=decision, needs_review=needs_review)
        )
    return decisions
