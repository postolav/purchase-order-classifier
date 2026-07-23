"""Shared record types used across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PORow:
    """A single normalized purchase-order line."""

    po: str
    supplier: str
    category: str
    currency: str
    amount: Optional[float]
    amount_eur: Optional[float]
    source_sheet: str
    row_index: int
    fx_flag: bool = False  # True if currency was unknown / amount unparsed


@dataclass
class Score:
    """The result of scoring one PO line against the KPMG taxonomy."""

    similarity: float
    confidence: float
    kpmg_category: Optional[str]
    reason: str
    source_stage: str  # "rules" | "llm" | "llm+web"


@dataclass
class Decision:
    """Final keep/discard + review gating for one line."""

    row: PORow
    score: Score
    decision: str  # "keep" | "discard"
    needs_review: bool = field(default=False)
