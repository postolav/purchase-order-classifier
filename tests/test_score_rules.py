from pathlib import Path

from po_classifier.kpmg_ref import load_taxonomy
from po_classifier.models import PORow
from po_classifier.score_rules import score_row

TAX = load_taxonomy(Path(__file__).parent.parent / "po_classifier" / "taxonomy.yaml")


def _row(category, supplier="ACME LTD"):
    return PORow(
        po="1", supplier=supplier, category=category, currency="EUR",
        amount=1000.0, amount_eur=1000.0, source_sheet="s", row_index=1,
    )


def test_clear_include_kept():
    s = score_row(_row("COMPUTER/SERVICES"), TAX)
    assert s.similarity >= 0.55
    assert s.kpmg_category is not None


def test_consultants_kept():
    s = score_row(_row("CONSULTANTS/CONTRACTS"), TAX)
    assert s.similarity >= 0.9
    assert "Consulting" in (s.kpmg_category or "")


def test_clear_exclude_discarded():
    s = score_row(_row("FUELS"), TAX)
    assert s.similarity < 0.3
    assert s.kpmg_category is None
    assert s.confidence >= 0.8


def test_audit_high_confidence():
    s = score_row(_row("Auditing & Accounting Services"), TAX)
    assert s.similarity >= 0.9
    assert s.confidence >= 0.8


def test_unknown_low_confidence():
    s = score_row(_row("SERVICES/DDFT"), TAX)
    # ambiguous -> should be a candidate for LLM (low-ish confidence)
    assert s.confidence <= 0.6
