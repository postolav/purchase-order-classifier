from po_classifier.fx import build_fx_table, parse_amount, to_eur


def test_parse_amount_variants():
    assert parse_amount(1234.5) == 1234.5
    assert parse_amount("653,092.38") == 653092.38
    assert parse_amount("€ 27,488.00") == 27488.00
    assert parse_amount("") is None
    assert parse_amount(None) is None
    assert parse_amount("n/a") is None


def test_build_fx_table_skips_headers():
    rows = [
        ("FX Rates (Avg 2025)", None),
        ("Currency", "EUR per 1 unit"),
        ("USD", 0.8862),
        ("GBP", 1.1672),
    ]
    fx = build_fx_table(rows)
    assert fx["EUR"] == 1.0
    assert fx["USD"] == 0.8862
    assert fx["GBP"] == 1.1672
    assert "Currency" not in fx


def test_to_eur_conversions():
    fx = {"EUR": 1.0, "USD": 0.8862}
    assert to_eur(100.0, "EUR", fx) == (100.0, False)
    assert to_eur(100.0, "USD", fx) == (88.62, False)
    # Unknown currency is flagged, not dropped.
    val, flagged = to_eur(100.0, "JPY", fx)
    assert val is None and flagged is True
    # Missing amount is flagged.
    assert to_eur(None, "EUR", fx) == (None, True)
