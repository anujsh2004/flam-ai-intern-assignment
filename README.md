# Flam AI Intern Assignment — The Audit

Audit of a prior tokenizer-fertility and serving-capacity report.

- `partA/` tokenizer audit (corpus, script audit, corrected analysis, memo)
- `partB/` capacity reconciliation (KV cache, throughput anomaly, goodput)
- `partC/memo.md` decision memo
- `NOTEBOOK.md` chronological lab notebook
- `starter_kit/` original provided files (unchanged)
- `docs/` project `plan.md`, `decision.md`, `state.md`
- `.claude/skills/flam-audit/` project workflow skill (`/flam-audit`)
- `.claude/skills/commit/` commit workflow skill (`/commit`)

Reproduction commands are added per part as each is completed. Current progress: see `docs/state.md`.

## Setup
```
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python partA/corpus/prep.py      # FLORES text: downloaded + hash-checked, not committed
```
F9 and the ablation use the gated `meta-llama/Llama-3.2-3B` tokenizer: accept its licence on Hugging Face and run `hf auth login`. Without access, the tests that need it skip with that instruction.

## Part A
- **A1 corpus:** `partA/corpus/README.md` (`python partA/corpus/stats.py`)
- **A2 audit:** `partA/A2_audit.md` (findings, evidence index), `partA/A2_results.md` (generated tables)
  ```
  python partA/fertility_v1.py --v0 --corpus eng=starter_kit/corpus_sample/eng_sample.txt --corpus hin=starter_kit/corpus_sample/hin_sample.txt
  python partA/audit/experiments.py F1 --tokenizer gpt2     # F1 F2 F3 F4 F6 F7 F8_graphemes F8_bytes; F9 --config v0|v1
  python partA/audit/ablation.py && python partA/audit/report.py
  python -m pytest partA/tests                    # full suite, incl. staleness checks of every committed number
  python partA/audit/mutation_check.py            # does every planted bug get caught?
  ```
- **Part C decision memo:** `partC/memo.md` (numbers from `python partC/arithmetic.py`; `python -m pytest partC/tests`)
- **Part B capacity:** `partB/answers.md` (B1–B4 with evidence index)
  ```
  python partB/capacity.py && python -m pytest partB/tests
  python partA/audit/mutation_check.py --names "B:" --tests partB/tests/test_capacity.py partB/tests/test_answers_evidence.py
  ```
- **A4 memo:** `partA/A4_memo.md` (coverage evidence: `python partA/analysis/coverage.py`)
- **A3 analysis:** `partA/A3_analysis.md` (the single cost number and why), `partA/A3_results.md` (generated tables)
  ```
  python partA/analysis/premium.py && python partA/analysis/report.py
  python partA/audit/mutation_check.py --names A3 --tests partA/tests/test_premium.py partA/tests/test_a3_report.py partA/tests/test_a3_evidence.py
  ```
