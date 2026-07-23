"""Currency -> EUR conversion using the workbook's References tab.

The References sheet looks like:

    FX Rates (Avg 2025) | None
    Currency            | EUR per 1 unit
    USD                 | 0.8862
    GBP                 | 1.1672
    ...

EUR is always 1.0 and need not be listed.
"""

from __future__ import annotations

import re
from typing import Dict, Optional


def parse_amount(raw) -> Optional[float]:
    """Parse an amount that may be a float or a thousands-separated string."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip()
    if not s:
        return None
    # Strip currency symbols and thousands separators; keep the decimal point.
    s = re.sub(r"[^\d.\-]", "", s.replace(",", ""))
    if s in ("", "-", "."):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def build_fx_table(references_rows) -> Dict[str, float]:
    """Build a {CURRENCY: eur_per_unit} map from the References sheet rows.

    `references_rows` is an iterable of tuples (as from openpyxl values_only).
    EUR is injected as 1.0. Non-numeric / header rows are skipped.
    """
    table: Dict[str, float] = {"EUR": 1.0}
    for row in references_rows:
        if not row or len(row) < 2:
            continue
        code, rate = row[0], row[1]
        if not isinstance(code, str):
            continue
        code = code.strip().upper()
        # Skip banners/headers like ("Currency", "EUR per 1 unit").
        if not re.fullmatch(r"[A-Z]{3}", code):
            continue
        try:
            table[code] = float(rate)
        except (TypeError, ValueError):
            continue
    return table


def to_eur(amount: Optional[float], currency: Optional[str], fx: Dict[str, float]):
    """Convert `amount` in `currency` to EUR.

    Returns (amount_eur, flagged) where flagged is True when the amount could not
    be converted (unknown currency or missing amount).
    """
    if amount is None:
        return None, True
    code = (currency or "EUR").strip().upper()
    rate = fx.get(code)
    if rate is None:
        return None, True
    return round(amount * rate, 2), False
