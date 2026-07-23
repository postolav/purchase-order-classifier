"""Command-line entry point for the Purchase Order classifier.

Usage:
    python -m po_classifier classify \
        --input "attachments/Work in Progress.xlsx" \
        --output out.xlsx \
        --config po_classifier/config.yaml

Add --no-llm for a fully offline, deterministic run (rules only), and --no-web to
disable web-search escalation while still using the LLM.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # dotenv is optional
    pass

from . import decide as decide_mod
from . import io_excel, pivots, score_llm, score_rules
from .kpmg_ref import load_taxonomy
from .llm import LLMScorer


def _load_config(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def cmd_classify(args) -> int:
    cfg = _load_config(args.config)
    if args.model:
        cfg["scoring"]["model"] = args.model
    if args.no_web:
        cfg["scoring"]["web_search"] = False

    tax_path = Path(args.config).parent / "taxonomy.yaml"
    tax = load_taxonomy(args.taxonomy or tax_path)

    print(f"Loading rows from {args.input} ...", file=sys.stderr)
    rows = io_excel.load_rows(args.input, cfg)
    print(f"  {len(rows)} rows loaded.", file=sys.stderr)

    print("Stage 1: deterministic scoring ...", file=sys.stderr)
    rule_scores = [score_rules.score_row(r, tax) for r in rows]

    llm_scores = {}
    if not args.no_llm:
        sc = cfg["scoring"]
        band = tuple(sc["review_band"])
        n_band = sum(1 for rs in rule_scores if score_llm.in_band(rs.confidence, band))
        print(f"Stage 2: LLM adjudication for {n_band} ambiguous rows ...", file=sys.stderr)
        scorer = LLMScorer(
            taxonomy_summary=tax.summary(),
            model=sc["model"],
            websearch_model=sc["websearch_model"],
            cache_dir=sc.get("cache_dir", "cache"),
            web_search=sc.get("web_search", True),
        )
        llm_scores = score_llm.adjudicate(
            rows, rule_scores, scorer, band,
            web_search=sc.get("web_search", True),
            max_llm_calls=sc.get("max_llm_calls", 400),
        )
    else:
        print("Stage 2 skipped (--no-llm).", file=sys.stderr)

    sc = cfg["scoring"]
    decisions = decide_mod.decide(
        rows, rule_scores, llm_scores,
        keep_threshold=sc["keep_threshold"],
        review_threshold=sc["review_threshold"],
    )
    kept = sum(1 for d in decisions if d.decision == "keep")
    review = sum(1 for d in decisions if d.needs_review)
    print(f"Kept {kept}/{len(decisions)}; {review} flagged for review.", file=sys.stderr)

    tables = pivots.build_pivots(decisions)
    io_excel.write_output(args.output, decisions, tables, cfg)
    print(f"Wrote {args.output}", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="po_classifier")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("classify", help="Classify a PO workbook.")
    p.add_argument("--input", required=True, help="Path to the input .xlsx")
    p.add_argument("--output", required=True, help="Path to write the output .xlsx")
    p.add_argument("--config", default="po_classifier/config.yaml", help="Path to config.yaml")
    p.add_argument("--taxonomy", default=None, help="Path to taxonomy.yaml (defaults next to config)")
    p.add_argument("--model", default=None, help="Override the Stage-2 model id")
    p.add_argument("--no-llm", action="store_true", help="Rules only; no API calls")
    p.add_argument("--no-web", action="store_true", help="Disable web-search escalation")
    p.set_defaults(func=cmd_classify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
