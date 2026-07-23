"""Build the four summary pivot tables over the KEPT rows.

Replicates the manual pivots from End Result.xlsx deterministically with pandas:
  Table 1 - Expenditure per service description (KPMG category)
  Table 2 - IT consulting expenditure per supplier
  Table 3 - Business consulting expenditure per supplier
  Table 4 - Audit services expenditure per supplier
"""

from __future__ import annotations

from typing import List

import pandas as pd

from .models import Decision

# Which KPMG categories feed each per-supplier table.
_IT_CATS = {
    "IT / ICT Consulting & Advisory",
    "Technology Implementation & Software",
    "IM&T Maintenance & Support",
    "ICT Services / Equipment",
}
_BUSINESS_CATS = {"Management / Business Consulting", "Risk / Deal Advisory", "Research & Analysis"}
_AUDIT_CATS = {"Audit & Assurance", "Tax & Accounting"}


def _kept_frame(decisions: List[Decision]) -> pd.DataFrame:
    rows = []
    for d in decisions:
        if d.decision != "keep":
            continue
        rows.append(
            {
                "supplier": d.row.supplier,
                "kpmg_category": d.score.kpmg_category or "Uncategorised",
                "amount_eur": d.row.amount_eur or 0.0,
            }
        )
    return pd.DataFrame(rows, columns=["supplier", "kpmg_category", "amount_eur"])


def _pct_table(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[group_col, "Sum of Amount", "Sum of Amount (%)"])
    g = df.groupby(group_col, dropna=False)["amount_eur"].sum().reset_index()
    total = g["amount_eur"].sum()
    g["Sum of Amount (%)"] = g["amount_eur"] / total if total else 0.0
    g = g.rename(columns={"amount_eur": "Sum of Amount"})
    g = g.sort_values("Sum of Amount", ascending=False).reset_index(drop=True)
    # Grand total row.
    grand = pd.DataFrame(
        [{group_col: "Grand Total", "Sum of Amount": total, "Sum of Amount (%)": 1.0 if total else 0.0}]
    )
    return pd.concat([g, grand], ignore_index=True)


def build_pivots(decisions: List[Decision]) -> dict[str, pd.DataFrame]:
    df = _kept_frame(decisions)
    it_df = df[df["kpmg_category"].isin(_IT_CATS)]
    biz_df = df[df["kpmg_category"].isin(_BUSINESS_CATS)]
    audit_df = df[df["kpmg_category"].isin(_AUDIT_CATS)]
    return {
        "Table 1 - Expenditure per Service Description": _pct_table(df, "kpmg_category"),
        "Table 2 - IT Consulting per Supplier": _pct_table(it_df, "supplier"),
        "Table 3 - Business Consulting per Supplier": _pct_table(biz_df, "supplier"),
        "Table 4 - Audit Services per Supplier": _pct_table(audit_df, "supplier"),
    }
