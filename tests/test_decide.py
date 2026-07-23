from po_classifier.decide import decide
from po_classifier.models import PORow, Score


def _row(idx):
    return PORow(po=str(idx), supplier="S", category="C", currency="EUR",
                 amount=1.0, amount_eur=1.0, source_sheet="s", row_index=idx)


def _score(sim, conf):
    return Score(similarity=sim, confidence=conf, kpmg_category="X",
                 reason="r", source_stage="rules")


def test_keep_and_review_gating():
    rows = [_row(1), _row(2), _row(3)]
    rule_scores = [_score(0.9, 0.9), _score(0.2, 0.9), _score(0.8, 0.4)]
    decisions = decide(rows, rule_scores, {}, keep_threshold=0.55, review_threshold=0.6)
    assert decisions[0].decision == "keep" and not decisions[0].needs_review
    assert decisions[1].decision == "discard" and not decisions[1].needs_review
    # High similarity but low confidence -> kept AND flagged for review.
    assert decisions[2].decision == "keep" and decisions[2].needs_review


def test_llm_overrides_rules():
    rows = [_row(1)]
    rule_scores = [_score(0.2, 0.5)]  # rules would discard
    llm = {1: _score(0.9, 0.95)}       # llm says keep
    decisions = decide(rows, rule_scores, llm, keep_threshold=0.55, review_threshold=0.6)
    assert decisions[0].decision == "keep"
    assert decisions[0].score.confidence == 0.95
