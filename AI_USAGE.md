# AI_USAGE

## How I used AI
I used **Claude Code** for most of the execution: reading the brief and sources, writing the code and tests, running every experiment, doing the arithmetic, and drafting every document.

**I directed it and owned the decisions.** Claude had to propose each step and wait for my approval. I chose:
- the corpus and the tokenizers;
- every finding's verdict;
- the thresholds and the ablation design;
- the B2 change;
- the Part C path;
- every commit and merge.

I am the sole author. The full chronology is in `NOTEBOOK.md`; decisions and evidence are in `docs/decision.md`.

## Mistakes Claude made, and how they were caught
| Mistake | Caught by | Fix |
|---|---|---|
| Recommended committing the FLORES text | Claude, on reading the licence terms | Not committed; regenerated with a hash check |
| Generalised a grapheme rule from one Hindi word | Cross-script test | Graphemes not used as the deciding unit |
| A broken "no Windows line endings" check hid a real CRLF bug | Git warning | Test-first fix |
| A2 tests had blind spots (4 of 14 planted bugs survived) | **My request for an evaluation round** | Gap tests; 14/14, later 50/50 |
| Mislabelled an XLM-R probe, and over-stated that XLM-R normalises text | Claude's own re-check | Harness split "tokens changed" from "any metric changed" |
| Wrong row in a hand-calculated test; flawed B4 logic | Failing test; review | Fixed |
| Wrong evidence citations in the A2 audit draft | Re-reading | Evidence index now verified by a test |
| A "fresh clone passed" result actually came from the wrong folder | Re-check | Discarded; found two real portability bugs, then fixed |
| Mutation-checker bugs (crash on Indic text, stale mutants, mis-targeted run, Part B not covered) | The runs themselves | Fixed; safeguard tests added |
| First production metric could not work (live traffic has no parallel English) | **My request to re-check it** | Replaced with tokens per code point by language and script |
| A pre-registered prediction was wrong for Hindi | Measurement | Recorded as wrong |

## How I kept it honest
- **Verification:** results were pre-registered before measuring, tested against hand-derived values, recomputed independently, guarded by staleness tests and evidence indexes, and checked by mutation testing.
- **Reproducibility:** a fresh clone passes all 363 tests.
