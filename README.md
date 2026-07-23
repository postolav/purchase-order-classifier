# Purchase Order Classifier

This tool takes the Department of Defence's purchase-order spreadsheet and
automatically sorts through every line to find the ones that look like
services KPMG could have provided — things like audit, tax, IT and business
consulting, ICT/advisory, or software and maintenance work.

Instead of someone manually reading through hundreds or thousands of rows,
the tool reads them for you, scores how likely each one is to be a "KPMG-type"
service, and hands back a new spreadsheet that's already sorted into:

- the lines it's confident **should be kept**,
- the lines it's confident **don't belong**, and
- a small pile of lines it **isn't sure about**, for a person to glance at.

It also flags anything unusual (missing data, unrecognised currencies, etc.)
so nothing gets silently dropped.

This guide assumes no prior technical experience. Follow the steps in order.

---

## What you'll need before starting

1. The purchase-order spreadsheet you want to process (an `.xlsx` file).
2. An **Anthropic API key** — this is what lets the tool ask Claude (the AI)
   to help make judgment calls on the tricky, ambiguous lines. If you don't
   have one, ask whoever manages your organisation's Anthropic/Claude account
   to create one for you. It looks like a long string of letters and numbers
   starting with `sk-ant-`.
3. About 15–20 minutes for the initial setup, plus however long a run takes
   (see "How long does it take?" below).

No prior coding knowledge is assumed for getting this project up and running. You will type a small number of
commands into a terminal window, but every command you need is given to you
exactly as you should type it.

---

## Step 1 — Install Python

The tool is written the Python programming language, so your computer
needs that installed first.

1. Go to [python.org/downloads](https://www.python.org/downloads/) and
   download the latest version (3.10 or newer).
2. Run the installer.
   - **On Windows:** on the very first screen of the installer, tick the box
     that says **"Add python.exe to PATH"** before clicking Install. This step
     is easy to miss and important — it's what lets you type `python` in a
     terminal later.
3. To confirm it worked, open a terminal:
   - **Windows:** press the Start key, type `PowerShell`, press Enter.
   - **Mac:** open **Terminal** from Applications → Utilities.
4. Type the following and press Enter:

   ```
   python --version
   ```

   You should see something like `Python 3.12.1`. If you instead see an
   error saying `python` isn't recognised, restart your computer and try
   again — this fixes it most of the time after a fresh install.

---

## Step 2 — Get the project files onto your computer

If someone has sent you this project as a folder (for example, a `.zip` file
or a folder called `purchase-order-classifier`), unzip it and place the
folder somewhere easy to find, such as your Desktop or Documents folder.

If instead you were given a link to a code repository (e.g. on GitHub), download it as a ZIP and unzip it the same way.

Either way, you should end up with a folder named `purchase-order-classifier`
containing things like `README.md` (this file), a `po_classifier` folder, and
a `requirements.txt` file.

---

## Step 3 — Open a terminal in the project folder

1. Open the `purchase-order-classifier` folder in your file explorer.
2. **Windows:** click into the address bar at the top of the folder window,
   type `powershell`, and press Enter — this opens a terminal already pointed
   at the right folder.
3. **Mac:** right-click the folder and choose "New Terminal at Folder" (or
   open Terminal and type `cd ` followed by dragging the folder into the
   window, then press Enter).

From now on, every command below should be typed into this terminal window.

---

## Step 4 — Install the tool's dependencies

The classifier relies on a handful of other free, well-established Python
libraries (for reading Excel files, talking to Claude, and so on). Install
them all in one go by typing:

```
pip install -r requirements.txt
```

Press Enter and wait. You'll see a scroll of text as things download and
install; this is normal. It usually takes one to two minutes. When it's
done, you'll be back at a plain prompt with no errors in red.

---

## Step 5 — Add your API key

The tool needs your Anthropic API key to be able to ask Claude for help on
ambiguous lines. You only need to do this once.

1. In the project folder, find the file named `.env.example`.
2. Make a copy of it in the same folder, and rename the copy to `.env`
   (note: just `.env`, with nothing before the dot).
   - Easiest way: back in the terminal, type:
     ```
     cp .env.example .env
     ```
3. Open the new `.env` file in a plain text editor (Notepad works fine).
4. You'll see a line like:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
   Replace the `sk-ant-...` part with your real API key, then save and close
   the file.

Keep this `.env` file private — it's linked to a paid account, similar to a
password. Never send it to anyone or upload it anywhere public.

---

## Step 6 — Add your spreadsheet

Put the purchase-order spreadsheet you want to process into the `attachments`
folder inside the project (create the folder if it isn't already there).

Make a note of its exact file name — you'll need to type it in the next step.

---

## Step 7 — Run the classifier

Back in the terminal, type the following, replacing `"Your File Name.xlsx"`
with the actual name of the spreadsheet you added in Step 6:

```
python -m po_classifier classify --input "attachments/Your File Name.xlsx" --output out.xlsx
```

Press Enter. You'll see progress messages appear, including a couple of
progress bars while the tool works through the spreadsheet. A full run
typically takes somewhere between a few minutes and about 20–25 minutes,
mostly depending on how many lines are ambiguous enough to need Claude's
input (see below).

When it finishes, you'll see a line like:

```
Wrote out.xlsx
```

That means it's done. A new file called `out.xlsx` will appear in the
project folder — this is your result.

### How long does it take?

- Lines that clearly do or don't match KPMG-type services are handled
  instantly using a built-in rulebook — no waiting.
- Only the genuinely unclear lines get sent to Claude for a closer look,
  which is slower (a few seconds each) but far more accurate for judgment
  calls. This is also the only part of the process that costs money, since
  it uses your API key.
- The tool remembers suppliers it has already looked up, so if you run it
  again later (e.g. on next quarter's file with overlapping suppliers), it
  will be faster and cheaper the second time.

---

## Step 8 — Review the results

Open `out.xlsx` in Excel (or Google Sheets, LibreOffice, etc.). You'll find
four tabs at the bottom:

1. **Scored Full List** — every single line from the original spreadsheet,
   with a similarity score and a confidence score added, plus the tool's
   reasoning for anything it sent to Claude.
2. **Filtered Kept** — just the lines the tool is confident belong in the
   KPMG-comparable category. This is likely the tab you actually want.
3. **Review Queue** — the small number of lines the tool wasn't confident
   about either way. Someone should give these a quick manual look. This tab
   has two columns for the decision: **Recommendation**, which is the tool's
   best guess (`keep` or `discard`), and **Decision**, which is left blank for
   you to fill in with your final call. Type `keep` or `discard` in the
   **Decision** column for each row after reviewing it. These decisions are
   worth keeping — in future they can be fed back in to make the tool more
   accurate over time (see "Future implementation" under "For technical
   readers").
4. **Pivot Summaries** — a rolled-up view of total spend by service type and
   by supplier, for a quick at-a-glance summary.

Nothing is ever deleted without notice. Every original line is still visible in
the "Scored Full List" tab, just labelled with the tool's assessment.

---

## Running it again next quarter/year

You can reuse this same setup for future spreadsheets. Just repeat Steps 6
and 7 with the new file — you don't need to reinstall anything or set your
API key again, since that only needs doing once.

If the layout of the source spreadsheet changes significantly (e.g. columns
are renamed or reordered), let whoever maintains this tool know, since it may
need a small adjustment to keep reading the file correctly.

---

## Troubleshooting

- **"python is not recognised..."** — Python isn't installed, or wasn't added
  to PATH. Reinstall it and make sure to tick the "Add to PATH" box (Step 1).
- **"pip is not recognised..."** — same cause and fix as above.
- **An error mentioning `ANTHROPIC_API_KEY`** — the `.env` file is missing or
  the key wasn't pasted in correctly. Revisit Step 5.
- **An error mentioning a missing file or "No such file"** — double-check the
  spreadsheet's file name and that it's inside the `attachments` folder,
  including matching the exact spelling and file extension.
- **It seems stuck / very slow** — this is usually normal for larger files
  the first time you run them, since each unfamiliar supplier needs a
  question sent to Claude. Subsequent runs are much faster.
- **Something else looks wrong** — you can always run the tool in a
  "no AI, rules only" mode to sanity-check that the basic setup works, by
  adding `--no-llm` to the command in Step 7. This won't need an API key and
  won't produce the fully-refined result, but it's a useful first check.

If you're stuck beyond this, reach out to whoever set up this tool for you
with a screenshot of the terminal and the error message shown.

---

## For technical readers

The sections above are written for a non-technical audience. If you're
comfortable with code, here's the shorter, technical summary.

### How it works — a tiered hybrid

1. **Load & normalize** — reads the raw workbook via config-driven column
   mapping (`config.yaml`), auto-detects the header row (skips banner rows),
   and FX-converts amounts to EUR using the workbook's `References` tab.
2. **Stage 1 — deterministic scorer** (`score_rules.py`) — keyword/fuzzy
   match against the curated KPMG taxonomy (`taxonomy.yaml`). Resolves the
   confident majority cheaply and reproducibly.
3. **Stage 2 — LLM adjudication** (`score_llm.py` + `llm.py`) — only the
   ambiguous middle band (Stage-1 confidence inside `review_band`) is sent to
   Claude for a structured `{similarity, confidence, kpmg_category, reason}`
   verdict. Genuinely unknown suppliers still uncertain after Stage 2 are
   escalated to a **cached Claude web search**.
4. **Decide & gate** (`decide.py`) — `keep` when similarity ≥
   `keep_threshold`; `needs_review` when confidence < `review_threshold`.
5. **Write output** (`io_excel.py`) — a workbook with four sheets: **Scored
   Full List**, **Filtered Kept**, **Review Queue**, **Pivot Summaries**
   (spend per service; IT/business consulting/audit per supplier).

### Flags

```
python -m po_classifier classify \
  --input "attachments/Work in Progress.xlsx" \
  --output out.xlsx \
  --config po_classifier/config.yaml
```

- `--no-llm` — rules only, fully offline and deterministic (no API key
  needed).
- `--no-web` — use the LLM but disable web-search escalation.
- `--model claude-opus-4-8` — override the Stage-2 model (default
  `claude-sonnet-5`; web-search escalations always use `claude-opus-4-8`).
- `--no-progress` — disable progress bars. (Bars also auto-disable when
  stderr is not a TTY, e.g. when output is piped or redirected, so logs stay
  clean.)

### Tuning what counts as "KPMG"

`po_classifier/taxonomy.yaml` is the single source of truth. Add/adjust
categories, include-keywords, and the exclude list; re-run.
`po_classifier/config.yaml` holds the thresholds (`keep_threshold`,
`review_band`, `review_threshold`) and the sheet/column mapping for next
year's file layout.

### Tests

```
python -m pytest -q
```

Covers FX conversion, the rule scorer, decision/gating, and an Excel
round-trip (load → normalize → write → reload).

### Notes

- The Stage-2 LLM cache lives under `cache/llm_scores.json`, keyed by
  (supplier, category, model, web_search), so re-runs and repeat suppliers
  are cheap and reproducible.
- The example input (`Work in Progress.xlsx`, 2025) and target
  (`End Result.xlsx`, 2024) are different years with different vocabularies,
  so a golden-file check is a directional sanity band, not an exact match.

### Future implementation — toward a continuously improving classifier

Today the tool classifies, but it has **no way to measure how accurate it is**, and
therefore no feedback loop to improve it. The following is a roadmap for closing that
loop. The central constraint shapes everything: **real accuracy metrics require labelled
ground truth (a trusted correct answer per line), which the system does not yet collect.**
So the work bootstraps labels first, and leans on label-free signals until enough labels
accumulate. The recommended direction is to source ground truth from **analysts' own
review decisions** (labels accrue as a byproduct of work they already do) and to use the
metrics primarily to **tune the system** (thresholds, taxonomy, prompts).

**Phase 1 — Capture ground truth (the prerequisite for everything else).**
Add an editable "Analyst verdict" column (keep / discard / blank) to the **Review Queue**
sheet in `po_classifier/io_excel.py` (`write_output`), plus a small loader that reads a
completed workbook back into `{row_key: verdict}`. This turns the human review that
already happens into a growing labelled dataset — no separate labelling project.
*Limitation:* it only covers the ambiguous review band, so it measures the hardest cases,
not overall accuracy; and it depends on analysts actually recording a verdict.

**Phase 2 — Label-free health metrics (work from day one, no ground truth needed).**
- **Review-queue rate & score distribution** — % kept / discarded / flagged and the spread
  of similarity/confidence scores per run (partly printed already in `cli.py`). *Why:*
  cheap regression and drift detection between quarters. *Limitation:* measures behaviour,
  not correctness — a confidently-wrong run can look perfectly healthy.
- **Reproducibility check** — re-run the same file and diff the output. *Why:* protects the
  deterministic-rerun property the LLM cache provides. *Limitation:* confirms consistency,
  not correctness.

**Phase 3 — Diagnostic accuracy (once labels exist).**
A new `po_classifier/metrics.py` that joins captured verdicts to the scored rows via a new
`metrics` subcommand (e.g. `python -m po_classifier metrics --scored out.xlsx --labels
reviewed.xlsx`), keeping measurement separate from classification.
- **Confusion matrix + Precision / Recall / F1** on the keep decision. *Why:* these map
  onto the two failure modes — low precision wastes analyst time, low recall silently drops
  KPMG-comparable spend. **Lead with recall**: dropped comparable spend is the costlier
  error for a competitive-analysis tool. *Limitation:* threshold-specific; the data is
  imbalanced (most lines are not comparable), so always report the precision/recall pair,
  never F1 alone.
- **Per-stage / per-category breakdown** — the same metrics sliced by `source_stage`
  (`rules` / `llm` / `llm+web`, already recorded) and `kpmg_category`. *Why:* localises
  where errors concentrate so tuning effort is targeted. *Limitation:* slices get noisy
  with few labels.

**Phase 4 — Tuning tools (when the label set is large enough to trust).**
- **Confidence calibration** — check that a 0.7 confidence really means ~70% correct
  (reliability curve / expected calibration error). *Why:* the human-in-the-loop design
  hinges on `review_threshold`; poor calibration makes that routing arbitrary. *Limitation:*
  needs labels across the full confidence range; rule-stage confidences are hand-assigned
  constants in `score_rules.py`, so expect them to calibrate worse than LLM confidences —
  a useful finding, not a bug.
- **Threshold sweep / precision-recall curve** — compute precision & recall across the full
  0–1 range to set `keep_threshold` from evidence rather than a guess. *Why:* makes
  threshold-setting a deliberate business decision (how much recall do we need?).
  *Limitation:* overfits to a small sample — needs enough labels to generalise to next
  quarter.

**Cold-start caveat:** on day one there are zero verdicts, so only the Phase 2 label-free
metrics work. Do not present Phase 3–4 accuracy numbers until a meaningful sample of labels
has accumulated, and remember any evaluation against `End Result.xlsx` is 2024 vs a 2025
input (different suppliers) — an estimate, not a guarantee.

Each phase is independently useful and builds on the previous one, so the loop can be closed
incrementally: capture labels → watch health → measure accuracy → tune thresholds and
taxonomy → re-measure.
