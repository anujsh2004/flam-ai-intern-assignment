# Flam AI Intern Assignment — The Audit

An audit of a previous intern's tokenizer-fertility and serving-capacity report (`starter_kit/REPORT_v0.md`) before leadership makes routing and capacity decisions on it.

## Deliverables

| Part | Read this | What it answers |
|---|---|---|
| A1 | `partA/corpus/README.md` | Eval corpus: FLORES-200 eng/hin/kan/tam, 2,009 parallel sentences; size, domain, preprocessing, limits |
| A2 | `partA/A2_audit.md` (+ generated `partA/A2_results.md`) | 9 audited findings in `fertility.py` and REPORT_v0 §1, each with command, before/after and verdict |
| A3 | `partA/A3_analysis.md` (+ generated `partA/A3_results.md`) | Corrected comparison: 4 tokenizers × 5 denominators with CIs; the single number that should drive cost |
| A4 | `partA/A4_memo.md` | 1-page memo: headline numbers, routing, biggest caveat, production metric |
| B | `partB/answers.md` | B1 KV bytes/token and capacity; B2 anomaly and proposed change; B3 misread column and goodput; B4 counter |
| C | `partC/memo.md` | 1-page decision memo: casual Indic replies under the given constraints |
| — | `NOTEBOOK.md` | Chronological lab notebook: hypothesis → experiment → result → revision, including dead ends |
| — | `AI_USAGE.md` | Where AI helped and where it misled (written by the author) |

Every number in the write-ups carries an evidence ID, or is checked by a test against generated JSON. A test fails if any committed number is stale.

## Setup (once)

**Windows:** clone into a reasonably short folder. Under a very deep path, git's *own* `.git/hooks/*.sample` files exceed the 260-character limit (true of any repository). Alternatively run `git config --global core.longpaths true`. This repo's own paths are capped at 80 characters by a test.

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # Python 3.14; versions pinned
.venv/Scripts/python partA/corpus/prep.py                    # FLORES text: downloaded + SHA-256 checked, not committed (licence, D-11)
```

**Gated tokenizer:** A2/F9, A3 and A4 use the gated `meta-llama/Llama-3.2-3B` tokenizer as the FLM-4B proxy. Accept its licence on Hugging Face and run `hf auth login`. Without access, the tests that need it **skip** with that instruction; they never fail silently.

## Reproduce, in assignment order

```
# A1 corpus statistics
python partA/corpus/stats.py

# A2 audit: original script, corrected script with one flag per fix, measurements, ablation, report
python starter_kit/fertility.py --corpus eng=starter_kit/corpus_sample/eng_sample.txt --corpus hin=starter_kit/corpus_sample/hin_sample.txt
python partA/fertility_v1.py --v0 --corpus eng=starter_kit/corpus_sample/eng_sample.txt --corpus hin=starter_kit/corpus_sample/hin_sample.txt
python partA/audit/experiments.py F1 --tokenizer gpt2     # F1 F2 F3 F4 F6 F7 F8_graphemes F8_bytes; F9 --config v0|v1
python partA/audit/ablation.py && python partA/audit/report.py

# A3 corrected analysis, and A4 coverage evidence
python partA/analysis/premium.py && python partA/analysis/report.py
python partA/analysis/coverage.py

# Part B and Part C
python partB/capacity.py
python partC/arithmetic.py

# Everything is verified, including staleness of every committed number
python -m pytest partA/tests partB/tests partC/tests
```

**Test quality (mutation checks):** `python partA/audit/mutation_check.py` runs the full A2 set. Targeted runs:
- `--names A3 --tests partA/tests/test_premium.py partA/tests/test_a3_report.py partA/tests/test_a3_evidence.py`
- `--names "B:" --tests partB/tests/test_capacity.py partB/tests/test_answers_evidence.py`

## Repository map
- `starter_kit/`: the provided files, byte-identical to the originals and never edited.
- `partA/fertility_v1.py`: the corrected script. `--v0` reproduces the original exactly.
- `partA/audit/`: the A2 harness and results. `partA/analysis/`: A3/A4.
- `partA/corpus/`: A1. `partB/`, `partC/`: code, tests and generated results.
- `docs/plan.md`, `docs/decision.md`, `docs/state.md`: plan, decision log with evidence, and current state.
- `.claude/skills/`: the project workflow and commit skills used while building this.
