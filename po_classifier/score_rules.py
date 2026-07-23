"""Stage 1 — deterministic keyword/fuzzy scorer against the KPMG taxonomy.

Produces a similarity in [0,1], a best-matching KPMG category, and a rule-based
confidence. High confidence is assigned when a clear include OR a clear exclude
resolves the line; ambiguous middles get low confidence and are escalated to the LLM.
"""

from __future__ import annotations

from typing import Optional, Tuple

from rapidfuzz import fuzz

from .kpmg_ref import Taxonomy
from .models import PORow, Score


def _normalize(text: str) -> str:
    return " ".join(str(text or "").lower().replace("/", " ").replace(".", " ").split())


def _keyword_hit(haystack: str, keyword: str) -> bool:
    """Substring match, or fuzzy token-set match for multi-word keywords."""
    kw = keyword.lower()
    if kw in haystack:
        return True
    # Fuzzy fallback catches typos/spacing variants (e.g. "COMPUTER.NETWORK").
    return fuzz.token_set_ratio(kw, haystack) >= 90


def score_row(row: PORow, tax: Taxonomy) -> Score:
    text = _normalize(f"{row.category} {row.supplier}")

    best_weight = 0.0
    best_cat: Optional[str] = None
    for cat in tax.categories:
        if any(_keyword_hit(text, kw) for kw in cat.include):
            if cat.weight > best_weight:
                best_weight = cat.weight
                best_cat = cat.name

    excluded = any(_keyword_hit(text, kw) for kw in tax.exclude_keywords)

    # Resolve include vs exclude.
    if best_cat is not None and best_weight >= tax.exclude_override_floor:
        # Strong KPMG match wins even if an exclude keyword also appears.
        similarity, category, reason = best_weight, best_cat, f"Strong match: {best_cat}"
        confidence = 0.9
    elif excluded:
        similarity, category, reason = 0.05, None, "Matches an excluded (non-KPMG) category"
        confidence = 0.85
    elif best_cat is not None:
        similarity, category, reason = best_weight, best_cat, f"Keyword match: {best_cat}"
        # Moderate matches are less certain than override-floor ones.
        confidence = 0.55 if best_weight < 0.8 else 0.75
    else:
        similarity, category, reason = 0.15, None, "No KPMG keyword matched"
        confidence = 0.45  # genuinely uncertain -> candidate for LLM

    return Score(
        similarity=similarity,
        confidence=confidence,
        kpmg_category=category,
        reason=reason,
        source_stage="rules",
    )
