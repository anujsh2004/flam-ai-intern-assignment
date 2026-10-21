# Plan — "The Audit" (Flam AI Team Intern Assignment 2026)

Status of this file: living roadmap. Current position is in [state.md](state.md); rationale for choices is in [decision.md](decision.md).

## 1. Assignment requirements (verified against the original PDF, not only the Word summary)

Timebox ~10 focused hours / 5 days. Graded on thinking-per-hour. 30-min live defense (gate). Fabricated evidence = automatic fail.

| Part | Pts | Requirement (short) |
|---|---|---|
| A1 | 10 | Eval corpus: >=4 languages incl. English, Hindi, 2 Dravidian. Document source, size, domain, preprocessing, + one paragraph on what it cannot tell us |
| A2 | 20 | Audit `fertility.py`: code bugs, >=1 conceptual flaw, >=1 suspicious-but-fine item. Every claim needs command + before/after + one-sentence why. Unverified flaw = -5 each |
| A3 | 12 | Recompute on A1 corpus, >=2 tokenizers (one multilingual/Indic-aware), >=2 denominators; say which single number should drive routing/cost and why |
| A4 | 8 | 1-page memo: corrected headline numbers, routing recommendation, biggest caveat, one production metric |
| B1 | 7 | KV bytes/token exactly; max concurrent 4096-token seqs; check vs log |
| B2 | 6 | Anomaly in prompt=3584 sweep; mechanism from specific rows/columns; one change + quantitative prediction |
| B3 | 4 | The one misread column behind both REPORT claims; batch-24 goodput two independent ways; what report should have said |
| B4 | 3 | One serving metric that confirms B2 mechanism + expected value |
| C | 15 | 1-page decision memo (SFT / 1B rewriter / prompting) with labelled: assumptions, arithmetic, numeric success metric, kill criterion + deadline, day-1 experiment |
| Defense | 15 | Re-derive numbers, run script on pasted input, add a flag live, counterfactuals |

Also required: `NOTEBOOK.md` (chronological, with dead ends; graded).

### Deliverable layout (repo root = submission root)
```
NOTEBOOK.md  README.md  requirements.txt
partA/ (code, corpus prep, tests/, results, memo)   partB/ (calcs, tests/, answers)   partC/memo.md
starter_kit/  (original files, never edited)        docs/ (plan, state, decision)   .claude/skills/flam-audit/
```

## 2. Corrections to the Word breakdown
- The Word doc says the starter kit was missing; it is now available and has been read.
- It lists the SDE role PDF as a second source; that PDF was not in the assignment folder and is irrelevant to the work.
- It leaves bugs/column unnamed (correctly); the files are now inspected. Leads are listed in section 5 as **hypotheses only**, not findings.
- Ambiguities to resolve (tracked in decision.md): GB vs GiB in the KV budget; "grapheme cluster" library; whether Part C may assume a specific base model; the PDF's "10 hours" vs the breadth of work.

## 3. Phases

Each task: write test/BDD scenario -> see it fail -> implement -> pass -> log in NOTEBOOK.md -> update state.md -> small commit.

### Phase 0 — Foundation (this session) — branch `main`
- [x] Read PDF, Word doc, starter kit; inspect GitHub remote (empty) and working dir (empty)
- [x] docs/{plan,decision,state}.md, `.claude` skill, repo scaffold, .gitignore
- [x] Validate consistency; first commit on `main` (no push without approval)

### Phase 5 — B capacity reconciliation — branch `part-b-capacity`
Dependencies: none (only `bench/`). Moved after Part A per user recommendation: A has the longest dependency chain (A1->A3) and the network/install risk, so it goes first; B/C do not depend on A.
- B1: `partB/kv_capacity.py` + tests: bytes/token, per-seq bytes, budget -> max seqs; compare with `preempted_seqs`/`kv_cache_util`.
- B3: test that `reported_tok_s` formula is identified from the CSV (hypothesis H-B1); goodput two ways (output tokens / wall-clock; per-request rate x requests).
- B2: identify anomaly rows (24 -> 32 -> 48), mechanism via `preempted_seqs`, `kv_cache_util`, `itl_ms_p50`, `wall_clock_s`; propose change with numeric prediction.
- B4: one metric + expected value.
- Acceptance: every number reproducible by one command; tests pass; answers in `partB/answers.md`.

### Phase 1 — A1 corpus — branch `part-a-corpus`
Dependency: network/dataset access (verified). Source: FLORES-200 dev+devtest, 4 languages eng/hin/kan/tam (D-03, user-confirmed).
- [x] Research alternatives from primary sources (FLORES-101 paper, Petrov et al., IN22 repo, FLORES+ card) -> D-03 table
- [x] Access check (HTTP headers), download, SHA-256 recorded
- [x] Failing tests first (`partA/tests/test_corpus.py`, 23) -> `partA/corpus/prep.py` -> green
- [x] Text-unit helpers with hand-derived expected values (`partA/units.py`, `tests/test_units.py`); grapheme behaviour per script pinned (D-05)
- [x] Corpus stats generated, not hand-typed (`partA/corpus/stats.py` -> `stats.json`; `tests/test_corpus_stats.py` checks consistency and staleness)
- [x] `partA/corpus/README.md`: size, domain, preprocessing (with evidence), unit totals, sample-size check, limitations paragraph, licence
- [x] User decision D-11: FLORES text not committed for now (`.gitignore`); `.gitattributes` + pinned requirements (D-12)
- [x] Committed locally on `part-a-corpus` (foundation `bd21ead` on `main`; A1 `31f0e44`; LF fix `edd8a50`; docs commit follows)
- [x] Merge `part-a-corpus` -> `main` (`--no-ff`): `48f28fe`, 44 passed on `main`
- Acceptance: all `partA/tests` pass from a clean run of `prep.py` + `stats.py`; every README number traceable to `stats.json` or `manifest.json`.

### Phase 2 — A2 audit — branch `part-a-audit` (from `main` at `48f28fe`)
Pre-registered on 2026-10-21, **before any A2 measurement** (see D-13, D-14, D-04). The evidence rule applies to every verdict, including "fine": each finding records the claim, the line, the exact command, before/after numbers, direction, magnitude, a one-sentence why, and the verdict.

**Deliverables:**
- `partA/A2_audit.md` (mandatory): written findings plus an audit of REPORT_v0 §1 claims; numbers are taken only from generated results.
- `partA/A2_results.md`: generated by `partA/audit/run_audit.py` from `partA/audit/results.json`, with a staleness test.
- `partA/fertility_v1.py`: corrected script, one flag per fix, `--v0` reproduces the original. `starter_kit/` is never edited.

**Corpora:** toy (`starter_kit/corpus_sample`, what the report used) and FLORES eng/hin/kan/tam (A1).

**Tokenizers:**
- `gpt2`: held fixed to isolate script flaws.
- `xlm-roberta-base`: for the F3 (lowercase) and F4 (NFC) findings, because their effect depends on tokenizer-internal normalisation.
- Llama-3.2-3B tokenizer: proxy for FLM-4B, for F9 (D-04).

**Results order:** the reports first give each finding's isolated delta (one fix applied to v0). Next comes the **ablation, leave-one-out**: start from fully corrected v1, switch off one fix at a time, and record each fix's contribution with a note. The **cumulative** path (v0 -> +F1 -> +F3 -> +F4 -> +F2, then the F7 denominator) comes last. All measured tables sit at the end of the reports.

To-do (TDD; one granular commit per step):
- [x] 1. Housekeeping: state.md records the merge and the branch (`3a5f83d`)
- [x] 2. Pre-registration: this section + D-13, D-14, D-04, D-15 (Jev rejected)
- [ ] 3. Reproduce v0: characterisation test runs the unmodified `starter_kit/fertility.py` on the toy corpus and expects REPORT_v0's 1.27 / 7.45 (and 0.226 / 1.579). A mismatch becomes a finding.
- [ ] 4. `fertility_v1.py` skeleton: `--v0` output identical to the original on toy + FLORES
- [ ] 5. F1 `--split space|whitespace`: fake-tokenizer test -> code -> commit; measured delta -> commit
- [ ] 6. F3 `--lowercase/--no-lowercase`: test -> code; deltas under gpt2 and XLM-R
- [ ] 7. F4 `--nfc/--no-nfc`: test -> code; deltas under gpt2 and XLM-R
- [ ] 8. F2 `--aggregate macro|micro`: test -> code; delta
- [ ] 9. F5: remove the unused `random` seed; test proves output unchanged
- [ ] 10. F6 `--special-tokens`: test -> code; delta (possible false-fertility inflation)
- [ ] 11. F7/F8 `--denominator words|codepoints|graphemes|bytes|sentence` (reuse `partA/units.py`): test -> code; cost-ratio comparison
- [ ] 12. F9: Llama-3.2-3B proxy vs gpt2 ratios (needs HF access approval)
- [ ] 13. `run_audit.py`: isolated deltas, leave-one-out ablation, cumulative -> `results.json` + `A2_results.md`; staleness test
- [ ] 14. `A2_audit.md`: findings in evidence-rule format + REPORT_v0 §1 claim audit
- [ ] 15. NOTEBOOK / state / plan / decision update; merge to `main` only after approval

### Phase 3 — A3 corrected analysis — branch `part-a-analysis`
Dependencies: Phases 1-2. Tokenizer comparison per decision D-04 (e.g. gpt2/tiktoken as baseline vs an open Indic-aware tokenizer such as XLM-R, IndicBERT/IndicTrans-family, or Llama/Gemma-class). Denominators: words, grapheme clusters, UTF-8 bytes, per parallel sentence. Bootstrap CIs over sentences. Decide the single routing/cost number (hypothesis: tokens per parallel sentence / per unit of equal content, since parallel text holds meaning constant).

### Phase 4 — A4 memo — branch `part-a-memo`: 1 page, numbers pulled from generated results.

### Phase 6 — C memo — branch `part-c-memo`
Dependencies: none technical; arithmetic needs consistency (A100 hours, reviewer 20 h total over 2 wks; reviewer covers only Hindi+Kannada). Day-1 experiment and kill criterion must be concrete.

### Phase 7 — Finish — branch `finalize`
README with exact reproduce commands; NOTEBOOK.md complete with dead ends; defense prep (re-derive each number from scratch; practice live flag addition).

## 4. Git strategy
`main` = verified only. One short-lived branch per phase (names above), merged with `--no-ff` after tests pass and user approval. Commits: small, imperative messages, scope prefix (`partB:`, `docs:`). **No co-author or tool attribution trailers — user is the sole author.** No push/PR/merge to remote without explicit approval.

## 5. Candidate leads in `fertility.py` / REPORT_v0 (UNVERIFIED hypotheses — do not report until measured)
| ID | Lead | Possible class |
|---|---|---|
| H-A1 | `line.split(" ")` vs `split()`: double spaces in samples (`books  in`, `किताबें  अलमारी`) yield empty "words" | code bug |
| H-A2 | Per-line mean of ratios (macro) vs corpus total tokens / total words (micro) | code bug / method |
| H-A3 | `len(line)` counts code points, not graphemes; Devanagari matras inflate it | metric |
| H-A4 | Words as denominator across languages with different morphology/orthography (A1: same content = 1.17x English words in hin, 0.74x kan, 0.77x tam) | conceptual |
| H-A5 | gpt2 tokenizer is English-centric; byte-level BPE on Indic script | method |
| H-A6 | `.lower()` — suspicious but possibly harmless for Devanagari, matters for English | maybe harmless |
| H-A7 | NFC normalisation — suspicious; A1 found NFC changes ~9% of Hindi FLORES lines (decomposes nukta letters), so its effect on token counts must be measured | open — not obviously harmless |
| H-A8 | `random.seed(1337)` unused — harmless | harmless |
| H-A9 | Report claim "tok/char confirms tok/word" — they share the numerator, so not independent | reasoning flaw |
| H-A10 | Report claim "property of the script, not the tokenizer" contradicted by a second tokenizer | unsupported claim |
| H-B1 | `reported_tok_s` appears to count prompt+generated tokens ((prompt+gen)*N/wall) rather than useful generated tokens | misread column |
| H-B2 | Rows at batch 32/48 with `preempted_seqs`>0 and `kv_cache_util` ~0.97: throughput drops (KV exhaustion, recompute) | B2 mechanism |
| H-B3 | Linear scaling to batch 48 ignores KV limit | B3 |

(Back-of-envelope sanity check done only mentally for planning: KV = 2*28*8*128*2 = 114,688 B/token. To be verified by tests in Phase 1, not asserted.)

## 6. Experiments & comparisons
- Tokenizers (A3): >=2, chosen after availability check (decision D-04).
- Corpus source (A1): FLORES-200 vs alternatives (D-03).
- Grapheme segmentation library (D-05).
- Part C: choose between SFT / rewriter / prompting by arithmetic feasibility (D-07).

## 7. Acceptance criteria (global)
- Every claim has a command, before/after numbers, and a one-sentence justification.
- `pytest` passes; scripts rerun from a clean clone with documented commands.
- Docs (`plan`, `state`, `decision`) agree with the repo; no unverified "success" statements.
