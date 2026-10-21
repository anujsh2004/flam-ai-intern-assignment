# Project state

_Last updated: 2026-10-21 (A1 committed locally on `part-a-corpus`; merge into `main` awaiting approval)_

## Current phase / task
Phase 1 — A1 corpus: **done and committed locally** on `part-a-corpus`. Next: merge it into `main` (`--no-ff`, after approval), then Phase 2 (A2) on `part-a-audit`. Order: A1 -> A2 -> A3 -> A4 -> B -> C (D-10).

## Completed
- **Phase 0 foundation.** Git history was reset at the user's request on 2026-10-21 and restarted the same day.
- **A1:**
  - **Research:** primary sources read; alternatives compared in D-03.
  - **Corpus:** FLORES-200 tarball hash-verified; eng/hin/kan/tam × dev+devtest = 2,009 parallel sentences.
  - **Code:** `prep.py`, `units.py` and `stats.py`, written TDD.
  - **Docs:** corpus README with limitations.
  - **Fix:** a Windows CRLF bug in the generated JSON (commit `edd8a50`).

## Git (local only; no pushes; `origin` configured but untouched)
| Commit | Branch | Message | Authored | Committed |
|---|---|---|---|---|
| `bd21ead` | `main` | chore: project scaffold, starter kit originals, workflow skills | 10-20 23:42 | 10-21 12:12 |
| `31f0e44` | `part-a-corpus` | partA: A1 evaluation corpus (FLORES-200) with tests | 10-21 00:26 | 10-21 12:13 |
| `edd8a50` | `part-a-corpus` | partA: write generated JSON with LF on every platform | 10-21 12:16 | 10-21 12:18 |
| `4bedafe` | `part-a-corpus` | docs: A1 notebook, decisions, plan and state | 10-21 12:19 | 10-21 12:20 |

- **Branch tips:** `main` = `bd21ead`; `part-a-corpus` = `4bedafe`. Merge not done.
- **Dates:** author dates = newest file time in each commit (user's choice); commit dates = real commit times.
- **Authorship:** all four commits are authored by `anujsh2004` only. 0 matches for co-author or tool attribution in any message.
- **Working tree:** clean, except this file and `NOTEBOOK.md`, which were rewritten after `4bedafe` and are **not yet committed**.

## What is (and isn't) in git
- **`main`:** `.gitignore`, `.gitattributes`, pinned `requirements.txt`, `README.md`, `.gitkeep` files, `starter_kit/**` (byte-identical to the provided kit, checked with `cmp`), `.claude/skills/{flam-audit,commit}`.
- **`part-a-corpus` adds:**
  - `partA/units.py`
  - `partA/corpus/{prep.py, stats.py, stats.json, README.md}`
  - `partA/corpus/prepared/manifest.json`
  - `partA/tests/*`
  - `NOTEBOOK.md`, `docs/*`
- **Never committed:**
  - FLORES sentence text, `prepared/*.txt` and `*.tsv` (D-11; regenerate with `prep.py`)
  - `partA/corpus/raw/`
  - `.venv/`, caches
- **Deleted at the user's request:** `AI_USAGE.md`. The assignment requires it, and the user has been told.

## Tests run / experiments
- `.venv/Scripts/python -m pytest partA/tests` gives **44 passed**. Per file: `test_corpus.py` 23, `test_units.py` 13, `test_corpus_stats.py` 8. This was the result immediately before commits `edd8a50` and `4bedafe`.
- **A1 findings:**
  - Alignment margins: number match 99.2–99.7%, length ratio 0.49–2.03.
  - NFC changes ~9% of Hindi lines (nukta letters).
  - The grapheme conjunct rule differs by script (Kannada and Tamil split).
  - Denominator ratios vs English: words 0.74–1.17×, bytes 2.56–3.19×, code points 1.00–1.17×.
  - Codepoint-ratio CI ±~0.7%; clustered ≈ i.i.d.
- **Line endings, measured:**
  - Committed blobs have 0 CR bytes, except `starter_kit/bench/bench_log.csv`, which is CRLF in the *original* kit (14 CR in 14 lines) and is preserved by `-text`.
  - All other starter files are LF.

## Decisions
- **Decided:** D-01 layout (ack pending), D-02 Python 3.14 venv, D-03 FLORES-200, D-05 regex `\X` with caveat, D-08 sole authorship, D-10 A-first, D-11 FLORES text not committed (for now), D-12 line endings and pins.
- **Provisional:** D-06.
- **Open:** D-04, D-07, D-09.

## Environment facts (checked)
- **Venv:** `.venv` on Python 3.14.0 with pytest 9.1.1, regex 2026.9.29, tiktoken 0.14.0, tokenizers 0.23.3, transformers 5.20.2, numpy 2.5.4, pandas 3.0.6 (pinned). No torch.
- **Unicode:** unidata 16.0.0.
- **Git:** `core.autocrlf=true` on this machine; `.gitattributes` overrides it.
- **Accounts:** `gh` logged in as anujsh2004. The user has a Hugging Face account, not yet configured here.

## Blockers / open issues
- Merge approval for `part-a-corpus` -> `main`.
- D-01 layout still awaiting an explicit ack.
- `AI_USAGE.md` (required deliverable) absent by user decision.

## Next steps
1. Commit this `state.md` and the `NOTEBOOK.md` update (needs approval).
2. Merge `part-a-corpus` -> `main` (`--no-ff`) after approval.
3. Phase 2 (A2): isolated experiments on `fertility.py` on branch `part-a-audit`. Note for A2/B: `bench_log.csv` is CRLF, and `fertility.py` reads text with `strip()`.
