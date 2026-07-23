# Purchase Order Classifier

Automates the manual filtering of an Irish Department of Defence purchase-order
spreadsheet down to entries that fall under a service category **comparable to KPMG's
offering** (audit, tax, IT/business consulting, ICT/advisory, software & maintenance).
Every line gets a **similarity score** and a **confidence score**; low-confidence lines
are routed to a human-review queue.

## How it works — a tiered hybrid

1. **Load & normalize** — reads the raw workbook via config-driven column mapping
   (`config.yaml`), auto-detects the header row (skips banner rows), and FX-converts
   amounts to EUR using the workbook's `References` tab.
2. **Stage 1 — deterministic scorer** (`score_rules.py`) — keyword/fuzzy match against the
   curated KPMG taxonomy (`taxonomy.yaml`). Resolves the confident majority cheaply and
   reproducibly.
3. **Stage 2 — LLM adjudication** (`score_llm.py` + `llm.py`) — only the ambiguous middle
   band (Stage-1 confidence inside `review_band`) is sent to Claude for a structured
   `{similarity, confidence, kpmg_category, reason}` verdict. Genuinely unknown suppliers
   still uncertain after Stage 2 are escalated to a **cached Claude web search**.
4. **Decide & gate** (`decide.py`) — `keep` when similarity ≥ `keep_threshold`;
   `needs_review` when confidence < `review_threshold`.
5. **Write output** (`io_excel.py`) — a workbook with four sheets: **Scored Full List**,
   **Filtered Kept**, **Review Queue**, **Pivot Summaries** (spend per service; IT /
   business consulting / audit per supplier).

## Install

```bash
pip install -r requirements.txt
cp .env.example .env      # then put your ANTHROPIC_API_KEY in .env
```

## Run

```bash
python -m po_classifier classify \
  --input "attachments/Work in Progress.xlsx" \
  --output out.xlsx \
  --config po_classifier/config.yaml
```

Flags:

- `--no-llm` — rules only, fully offline and deterministic (no API key needed).
- `--no-web` — use the LLM but disable web-search escalation.
- `--model claude-opus-4-8` — override the Stage-2 model (default `claude-sonnet-5`;
  web-search escalations always use `claude-opus-4-8`).

## Tuning what counts as "KPMG"

`po_classifier/taxonomy.yaml` is the single source of truth. Add/adjust categories,
include-keywords, and the exclude list; re-run. `po_classifier/config.yaml` holds the
thresholds (`keep_threshold`, `review_band`, `review_threshold`) and the sheet/column
mapping for next year's file layout.

## Tests

```bash
python -m pytest -q
```

Covers FX conversion, the rule scorer, decision/gating, and an Excel round-trip
(load → normalize → write → reload).

## Notes

- The Stage-2 LLM cache lives under `cache/llm_scores.json`, keyed by
  (supplier, category, model, web_search), so re-runs and repeat suppliers are cheap and
  reproducible.
- The example input (`Work in Progress.xlsx`, 2025) and target (`End Result.xlsx`, 2024)
  are different years with different vocabularies, so a golden-file check is a directional
  sanity band, not an exact match.
