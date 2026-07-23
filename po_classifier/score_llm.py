"""Stage 2 — adjudicate the ambiguous middle band with the LLM.

Only lines whose Stage-1 confidence falls inside `review_band` are sent. Web-search
escalation fires when the Stage-2 result is still uncertain for an unknown supplier.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from .llm import LLMScorer
from .models import PORow, Score


def in_band(conf: float, band: Tuple[float, float]) -> bool:
    lo, hi = band
    return lo <= conf <= hi


def adjudicate(
    rows: List[PORow],
    rule_scores: List[Score],
    scorer: LLMScorer,
    review_band: Tuple[float, float],
    web_search: bool,
    max_llm_calls: int,
    progress: Optional[Callable[[], None]] = None,
) -> Dict[int, Score]:
    """Return {row_index: llm_score} for the subset that was escalated.

    Escalation policy:
      1. Stage-1 confidence in the middle band -> LLM (no web).
      2. If the LLM is still low-confidence, escalate that supplier to a web lookup.

    `progress`, if given, is called exactly once per in-band row processed (so a caller
    can advance a progress bar). It is kept generic so this module stays free of any
    specific bar library.
    """
    out: Dict[int, Score] = {}
    calls = 0
    # Cache web decisions per supplier so we don't web-search the same firm twice.
    web_done: set[str] = set()

    for row, rs in zip(rows, rule_scores):
        if not in_band(rs.confidence, review_band):
            continue
        if calls >= max_llm_calls:
            break
        calls += 1

        r = scorer.score(row.supplier, row.category, row.amount_eur, rs.kpmg_category, use_web=False)

        # Escalate genuinely uncertain unknown suppliers to a web lookup.
        supplier_key = row.supplier.strip().lower()
        if (
            web_search
            and r["confidence"] < review_band[0]
            and supplier_key not in web_done
            and calls < max_llm_calls
        ):
            web_done.add(supplier_key)
            calls += 1
            r = scorer.score(
                row.supplier, row.category, row.amount_eur, rs.kpmg_category, use_web=True
            )

        out[row.row_index] = Score(
            similarity=r["similarity"],
            confidence=r["confidence"],
            kpmg_category=r["kpmg_category"],
            reason=r["reason"],
            source_stage=r["source_stage"],
        )
        if progress is not None:
            progress()
    return out
