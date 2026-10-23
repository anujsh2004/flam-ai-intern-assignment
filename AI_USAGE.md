# AI_USAGE

## Summary
I used **Claude Code** for most of the execution: reading the brief and sources, writing code and tests, running every experiment, doing the arithmetic, and drafting the documents.

**Every decision was mine.**
- **Before any step was executed:** Claude proposed it and waited for my approval.
- **Where there was a choice:** I made it.
- **Commits, merges and pushes:** I approved each one, and I am the sole author.
- **Testing:** every task ended with tests before it was committed.

## Where AI was used, and to what extent

| Part | What Claude did (extent: most of the execution) | What I decided |
|---|---|---|
| Setup and process | Read the brief, my notes and the starter kit; wrote the plan, decision log and state files | Order: **Part A before Part B**. Discuss before every step. Sole authorship. Small commits. Nothing pushed without approval. |
| A1 corpus | Researched corpus options from primary sources; wrote the download/prep and stats code and the corpus README | **FLORES-200**, **4 languages**; **do not commit the FLORES text** (licence) |
| A2 audit | Wrote the corrected script (one flag per fix), the measurement harness and the ablation; ran all measurements; drafted the audit | Every finding's **verdict** (pre-registered); **my rule for F9**; test F6 properly; accepted F1's revision; **ablation design** (leave-one-out first); asked for an **evaluation round** of the tests |
| A3 analysis | Wrote the premium/bootstrap module; measured 4 tokenizers × 5 denominators; drafted the analysis | The **single-number** criterion; **IndicBERT v2**; **Sarvam-1 not needed**; asked **why Kannada/Tamil cost more** (this became A4's evidence) |
| A4 memo | Wrote the coverage script; drafted the memo | Approved the routing recommendations; asked to **re-check the caveat and the metric** (the metric was replaced) |
| Part B | Wrote and tested the calculations; drafted the answers | GB-vs-GiB approach; **B3 method B**; **evaluate all three B2 changes first**; chose the **cap at 24** with fp8 as follow-up |
| Part C | Wrote the tested arithmetic; drafted the memo | **Prompting to launch, LoRA SFT as fallback, rewriter rejected**; Hindi + Kannada first; thresholds, kill dates, reviewer rate |
| Time trade-offs | Estimated the cost of each option | Targeted mutation runs for A3/B; waived the final full mutation run |

## Testing after every task
- **Test-first:** every calculation was written test-first, with hand-derived expected values.
- **Before each commit:** the relevant tests ran; the **full suite** ran before every merge.
- **No stale numbers:** staleness tests re-derive every committed number, and evidence indexes in A2, A3 and Part B are checked by tests, with negative checks.
- **Independent checks:** F1 recomputed with no project code (difference 0); the A3 bootstrap cross-checked against A1's.
- **Mutation testing:** planted bugs must be caught. A2 50/50; A3 12/12; Part B 10/10.
- **Reproducibility:** a fresh `git clone` passed 363/363 tests; the suite on `main` now has **381 tests, all passing**.

## Mistakes Claude made, and how they were caught

| Mistake | Caught by | Fix |
|---|---|---|
| Recommended committing the FLORES text | Claude, reading the licence terms | Not committed; regenerated with a hash check |
| Generalised a grapheme rule from one Hindi word | Cross-script test | Graphemes not used as the deciding unit |
| A broken "no Windows line endings" check hid a real CRLF bug | Git warning | Test-first fix |
| A2 tests had blind spots (4 of 14 planted bugs survived) | **My evaluation-round request** | Gap tests; 14/14, later 50/50 |
| Mislabelled an XLM-R probe and over-stated its normalisation | Claude's re-check | Harness split "tokens changed" from "any metric changed" |
| Wrong row in a hand-calculated test; flawed B4 logic | Failing test; review | Fixed |
| Wrong evidence citations in the A2 draft; four findings missing the evidence-rule format | Re-reading; **my submission check** | Fixed; both now verified by tests |
| A "fresh clone passed" result came from the wrong folder | Re-check | Discarded; found and fixed two portability bugs |
| Mutation-checker bugs (Indic-text crash, stale mutants, mis-targeted run, Part B not covered) | The runs themselves | Fixed; safeguard tests added |
| First production metric could not work (no parallel English in live traffic) | **My re-check request** | Replaced with tokens per code point by language and script |
| A pre-registered prediction was wrong for Hindi | Measurement | Recorded as wrong |

The full chronology, including dead ends, is in `NOTEBOOK.md`; each decision and its evidence is in `docs/decision.md`.
