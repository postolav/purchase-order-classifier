"""The progress callback must fire exactly once per in-band row, and adjudicate must
work without any real API calls (stub scorer)."""

from po_classifier.models import PORow, Score
from po_classifier.score_llm import adjudicate

BAND = (0.35, 0.70)


class StubScorer:
    """Stands in for LLMScorer.score — no network, high-confidence verdict so no
    web escalation fires."""

    def __init__(self):
        self.calls = 0

    def score(self, supplier, category, amount_eur, tentative, use_web=False):
        self.calls += 1
        return {
            "similarity": 0.8,
            "confidence": 0.9,  # >= band low, so no web escalation
            "kpmg_category": "Management / Business Consulting",
            "reason": "stub",
            "source_stage": "llm+web" if use_web else "llm",
        }


def _row(idx):
    return PORow(po=str(idx), supplier=f"S{idx}", category="C", currency="EUR",
                 amount=1.0, amount_eur=1.0, source_sheet="s", row_index=idx)


def _score(conf):
    return Score(similarity=0.5, confidence=conf, kpmg_category=None,
                 reason="r", source_stage="rules")


def test_progress_called_once_per_in_band_row():
    rows = [_row(1), _row(2), _row(3), _row(4)]
    # Confidences: in-band, out-of-band (too high), in-band, out-of-band (too low).
    rule_scores = [_score(0.5), _score(0.95), _score(0.4), _score(0.1)]
    in_band_count = 2

    ticks = []
    result = adjudicate(
        rows, rule_scores, StubScorer(), BAND,
        web_search=False, max_llm_calls=100,
        progress=lambda: ticks.append(1),
    )

    assert len(ticks) == in_band_count
    assert len(result) == in_band_count  # only in-band rows produce scores


def test_progress_optional_default_none():
    rows = [_row(1)]
    rule_scores = [_score(0.5)]
    # No progress kwarg -> must not raise.
    result = adjudicate(rows, rule_scores, StubScorer(), BAND,
                        web_search=False, max_llm_calls=100)
    assert len(result) == 1
