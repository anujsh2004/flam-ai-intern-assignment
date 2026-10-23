# AI_USAGE

## How I worked with AI

I used **Claude Code** throughout this assignment. Most of the hands-on work was done by the AI under my direction: code, tests, experiment runs, arithmetic, and first drafts of every document. **The direction, the decisions and the accountability were mine.**
- **Before anything was built:** I set the working rules.
  - The AI had to discuss each step with me before executing it.
  - Every claim needed a reproducible experiment (the assignment's evidence rule).
  - Decisions were recorded with alternatives and evidence (`docs/decision.md`).
  - Test-driven development throughout.
  - Small commits, with me as the sole author.
- **At every decision point:** the AI stopped and asked. I chose the corpus, the tokenizers, the verdict for each finding, the thresholds, the ablation design, the B2 change, the Part C path, and when to merge.
- **Every commit and merge:** made only with my approval. Nothing was pushed without my go-ahead.

`NOTEBOOK.md` records the chronology, including the dead ends.

## Where AI helped

| Area | What the AI did | My part |
|---|---|---|
| Understanding the brief | Read the PDF, my Word breakdown and the starter kit. Separated what the brief requires from my notes. Listed ambiguities. | Supplied the materials. Corrected the plan's order (Part A before Part B). |
| Research | Read the primary sources for corpus and tokenizer choices (FLORES-101 paper, Petrov et al., IN22, the FLORES+ licence; Hugging Face licence and access checks). Checked the tools I asked about: Jev, IndicConformer, Sarvam-1. | Chose FLORES-200, IndicBERT v2 and the Llama-3.2-3B proxy. Decided Sarvam-1 was not needed. Obtained the gated Llama access. |
| Code and tests | Wrote the corpus prep, the corrected `fertility_v1.py` (one flag per fix), the measurement harness, ablation, A3 premium/bootstrap, Part B capacity and Part C arithmetic, each test-first with hand-derived expected values. | Approved each step and asked for evaluation rounds (below). |
| Experiments | Ran every measurement and recorded exact commands and before/after numbers. | Set what each experiment had to show, and the order the results are reported in. |
| Verification tooling | Built staleness tests (every committed number is re-derived), evidence indexes checked by tests, a mutation checker, fresh-clone checks. | Asked for a proper evaluation of A2 before continuing, which is what produced this layer. |
| Writing | Drafted the audit, analyses, memos, Part B answers, README and decision log. | Reviewed and approved them. Set the scope of each memo. |

## Where the AI got things wrong, and how each was caught and fixed

| # | What went wrong | How it was caught | What changed | Ref |
|---|---|---|---|---|
| 1 | Recommended committing the FLORES sentence text to the repo | AI, after reading the FLORES+ terms (no redistribution) | **I decided** not to commit it; `prep.py` regenerates it with a hash check | D-11 |
| 2 | Generalised from one Hindi word that the grapheme counter merges conjuncts in all scripts | AI cross-script test | Kannada/Tamil behave differently, so graphemes were not used as the deciding denominator | D-05 |
| 3 | Claimed there were no Windows line endings (the check command itself was broken); the generated JSON actually had CRLF | `.gitattributes` warning while committing | Test-first fix (`newline="\n"`); the slip is recorded in the notebook | `edd8a50` |
| 4 | My A2 tests had blind spots: 4 of 14 planted bugs survived | **My request for a proper evaluation round** | Gap tests added (14/14). Design fixes: single source of defaults, `--v0` as a base, per-language verdicts, fresh-clone skips | `19aee1b`, `ded8448`, `2532cea` |
| 5 | Printed "XLM-R lowercases internally: True" when the test meant the opposite | AI re-reading its own probe | Corrected; that is why F3 could be measured under XLM-R | NOTEBOOK |
| 6 | Claimed XLM-R normalises text internally; the harness said 183 lines "changed" | AI direct probe | The harness was mixing "tokens changed" with "tok/char changed", so it was split into tokens / words / any metric | `cd79142` |
| 7 | The mutation checker crashed on Indian-language test output (cp1252 decoding) | The crash itself | Reproduced the exact error test-first (third try) and fixed | `d5c6ccb` |
| 8 | Changed code without updating a mutant, which aborted a long run | The run's own safeguard | Added a fast test that every mutant still matches the code | `95f030c` |
| 9 | A hand-calculated test value used the wrong log row (batch 16 instead of 24) | The test failed | Fixed the test, not the code | `4c86038` |
| 10 | Part B's B4 logic compared the cap with itself (always "0") | AI review | Rewritten against the 25 sequences that fit, with a test that a cap of 30 cannot promise 0 | `7521736` |
| 11 | Wrong evidence citations in the first A2 audit draft, and one number with no evidence ID | AI re-reading the draft | Fixed; the evidence index is now verified by a test | `61cd46b` |
| 12 | A pre-registered prediction failed: "the sentence premium lies between per-word and per-byte" is false for Hindi | Measurement | Recorded as wrong, not explained away | D-18 |
| 13 | A "fresh clone: 194 passed" result actually came from the repo, not the clone | AI re-checking where the command ran | Discarded. Found two real bugs: result filenames too long for Windows, and a test marker moved onto the wrong test | `0e88633` |
| 14 | First mutation run for A3 targeted the wrong code (selected by file, pulling in slow A2 mutants) | AI noticed the scale | Stopped; switched to selecting by name | `6d7b53f` |
| 15 | The mutation checker never copied Part B, so Part B could not be mutated | AI | Fixed; Part B targeted run 10/10 | `0d6ec1e` |
| 16 | The first A4 production metric ("tokens per request vs English") cannot work, because live traffic has no parallel English | **My request to re-check the caveat and the metric** | Replaced by tokens per code point per language and script vs the FLORES baseline | A4 memo |
| 17 | Small editing slips: a scripted edit broke a file's syntax; a duplicated sentence in the notebook | Tests and AI re-reading | Fixed before commit | NOTEBOOK |

What the AI did **not** do: invent a source it could not find. When I asked about "CDM", it reported that nothing matched and asked me which one I meant.

## Decisions I made or reversed

| Topic | What the AI proposed | My decision | Effect |
|---|---|---|---|
| Authorship | Default AI co-author lines | Sole author, no AI attribution in commits | All commits are mine |
| Process | Proceed step by step | Discuss before every step; questions asked in chat | Every change approved |
| Order | Part B first (small, deterministic) | **Part A first** | The longest dependency chain and network risk were handled early |
| Verdicts | Candidate findings F1–F9 | I set each verdict: F1/F3 code bugs, F2 method flaw, F4 fine, F5 tech debt, **F6 to be tested**, F7/F8 conceptual, **F9 by my rule** (cost is our model's, so conceptual) | Pre-registered before measurement |
| F1 | — | Predicted a small blast radius; **accepted the revision to "material"** after it measured +2.78% on Kannada | D-13 |
| Ablation | Isolated + cumulative | **Leave-one-out from the fully corrected version first**, then cumulative | Showed F7 makes F1/F2 irrelevant |
| Speed | Full mutation run per step | Kept the full runs for A2. **Chose targeted runs** for A3/B on time grounds, and waived the final full run | D-19 |
| Indic tokenizer | IndicBERT v2; Sarvam-1 optional | Asked about IndicConformer (checked: a speech model, not applicable). **Sarvam-1 not needed.** | D-18 |
| Why Dravidian costs more | — | **I asked why.** That led to the coverage measurement (98.1% of Kannada tokens are byte fragments) | Became A4's evidence and its production baseline |
| B3 goodput | — | **Option B** after the AI found the log's clocks disagree | D-20 |
| B2 change | One proposal | **Evaluate all three first**; ranked by performance *and correctness*, then latency; chose the cap at 24 with fp8 as the follow-up | D-20 |
| Part C | Three paths | Prompt-only to launch, LoRA SFT as fallback, **rewriter rejected**. Launch Hindi + Kannada, the other four only after validation | D-07 |

My own premises were checked too. I said the corpus contained many blank lines; measurement showed none. The test was still added, for pasted input during the defense.

## How I made sure AI output was trustworthy
- **Pre-registration:** verdicts, thresholds and design were written down before any measurement, so results could not move the goalposts.
- **Test-first:** every calculation was tested with hand-derived values first.
- **Independent recomputation:** e.g. F1 recomputed with no project code, difference 0. The A3 bootstrap was cross-checked against A1's.
- **No stale numbers:** staleness tests re-derive every committed number. Evidence indexes (A2, A3, Part B) are verified by tests, with negative checks.
- **Mutation testing:** planted bugs must be caught (A2 50/50; A3 12/12; Part B 10/10, targeted).
- **Fresh clone:** 363 tests pass after setup, and the starter kit is byte-identical to the original.

I can re-derive the headline numbers and explain every decision above. Where the AI was wrong, the error, the catch and the fix are all in `NOTEBOOK.md`.
