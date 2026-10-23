# Project state

_Last updated: 2026-10-22 (A3 complete on `part-a-analysis`; merge into `main` awaiting user approval)_

## Current phase / task
Phase 3 — **A3 is complete** on branch `part-a-analysis` (from `main` at `c155ad7`, after the A2 merge). Next: the user approves the `--no-ff` merge, then A4 (memo). Order: A1 -> A2 -> A3 -> A4 -> B -> C (D-10).

## A4 outcome (branch `part-a-memo`; `partA/A4_memo.md`)
- **Headline:** hin 2.53×, kan 8.87×, tam 7.63× (serving tokenizer, per sentence).
- **Routing:** budget per language; the pressure is Dravidian (byte fallback); evaluate an Indic vocabulary; verify with FLM-4B's tokenizer first.
- **Caveat:** the proxy tokenizer, then the unmeasured domain mix.
- **Metric:** tokens per code point by language and script vs FLORES, ±20% weekly.
- **Merge:** pending user approval.
- **Reminder owed to the user:** offer the **defense cheat sheet** once the remaining work is done.

## Remaining after A4
1. Finalize: NOTEBOOK pass, README, state; starter-kit and fresh-clone checks; final full suite.
2. `AI_USAGE.md`, written by the user.
3. Push to GitHub, after user approval.
4. Defense cheat sheet: remind the user.

## Part C outcome (merged into `main` at `dfeace8`; `partC/memo.md`)
- **Recommendation:** (c) prompting is the launch path for hi+kn; (a) LoRA SFT on synthetic pairs is the fallback; (b) the rewriter is rejected (+24% decode work, ~19% fewer requests per L4).
- **Success:** ≥70% casual and ≥95% meaning on n=200.
- **Kill criteria:** day 5 / 50% -> switch to SFT; day 12 / 70% -> launch the best variant or defer.
- **Day 1:** 2 prompt variants, with 50 blind pairs also measuring reviewer speed.
- **Tests:** partC 27 passed. Merge pending user approval.

## Part B outcome (merged into `main` at `fc2a4a5`; details: `partB/answers.md`)
- **B1:** 114,688 B/token; about **25** concurrent 4096-token sequences (decimal GB, confirmed by two log checks).
- **B2:** goodput peaks at b24 then falls with preemption. **Proposed: cap at 24** (+23.8%, from logged data); fp8 KV is the follow-up experiment (D-20).
- **B3:** `reported_tok_s` counts prompt + gen. Honest b24 goodput is 200.92 / 200.93 tok/s. Log caveat: `e2e_p95` exceeds the wall clock on 12/13 rows.
- **B4:** `vllm:num_preemptions_total`.
- **Tests:** partB 68 passed; targeted mutation 10/10. Full suite before the merge.
- **Merge:** awaiting user approval (local only, no push).

## A3 outcome (details: `partA/A3_analysis.md`; tables: `partA/A3_results.md`)
- **Single cost number (D-06, decided on evidence):** tokens per parallel sentence vs English, ratio of totals, serving tokenizer (Llama-3.2-3B proxy):
  - hin **2.53** [2.50, 2.55];
  - kan **8.87** [8.77, 8.96];
  - tam **7.63** [7.55, 7.71].

  These are 95% article-clustered CIs.
- **Why:** parallel sentences hold content constant. On the same tokens, the other units give hin 2.16 (word), 3.86 (grapheme) and 0.99 (byte). The instrument matters about 6×: gpt2 7.44 vs IndicBERT 1.17.
- **Insight for A4:** the cost problem is **Dravidian** (kan/tam ≈ 3× Hindi's premium), not "Indic" as a whole.
- **Per-request BOS overhead:** small (2.53 -> 2.47).
- **Per-sentence spread** (hin): p10–p90 2.00–3.16.
- **Pre-registration check:** tokenizer ranking ✅. "Sentence between word and byte" ❌ for Hindi, recorded.
- **Verification:**
  - full suite 210 passed (before `c0b7f2f`);
  - targeted A3 mutation **12/12** (D-19);
  - bootstrap cross-checked against A1's;
  - 28 evidence IDs verified by a test.
- **Final full mutation run:** waived by the user (D-19, risk accepted).
- **Sarvam-1:** not needed.
- **Merge:** approved.
- **Why kan/tam are costlier:** Llama-3 vocabulary coverage. 98.1% / 89.2% of their tokens are byte fragments vs 0.2% for Hindi (to be committed as a script in A4).

## A2 (complete, merged into `main` at `c155ad7`)

## A2 outcome (details: `partA/A2_audit.md`; numbers: `partA/A2_results.md`)
| # | Finding | Verdict | Headline |
|---|---|---|---|
| F1 | `split(" ")` | code bug, material | kan fertility +2.78% when fixed |
| F2 | mean of per-line ratios | method flaw, material | kan −1.61% (gpt2) / −1.70% (XLM-R) |
| F3 | `.lower()` | code bug, material | hin/eng ratio +3.57% (gpt2) / +1.73% (XLM-R) |
| F4 | NFC | looks suspicious but fine | ≤0.11% |
| F5 | unused `random.seed` | technical debt | no effect (proven), removed |
| F6 | `add_special_tokens=False` | looks suspicious but fine | flipping it would inflate up to +23.74% |
| F7 | tokens per word | conceptual, material | FLORES gpt2 hin 6.10 -> 7.18, kan 17.40 -> 13.11 per sentence |
| F8 | tok/char "confirms" | conceptual, material | hin 2.77×–10.89× depending only on the unit |
| F9 | gpt2 as the instrument | conceptual, largest | V1 hin 7.44 -> 2.53 with the Llama-3.2-3B proxy for FLM-4B |

- **Ablation:** F7 subsumes F1/F2 in V1 (exactly 0.00%). F3 survives.
- **Report claims:** "~6× cost", "metrics agree", "property of the script" and "more chars per word" are all refuted with evidence.
- **Corrected headline (proxy tokenizer, FLORES, per parallel sentence):** hin ≈ 2.53×, kan ≈ 8.87×, tam ≈ 7.63× English.

## Verification (all run, outputs read)
- **Full suite:** `.venv/Scripts/python -m pytest partA/tests` -> **196 passed** before `0e88633` (about 4–6 min per run).
- **Mutation:** `python partA/audit/mutation_check.py` -> **50/50 killed** (baseline 150 A2 tests), covering every A2 module including the ablation, report, Llama skip and file naming.
- **Independent recompute:** F1 recomputed with no project code: max difference 0.
- **Staleness:** every committed result JSON, `ablation.json`, `A2_results.md`, `stats.json` and the 46 audit evidence IDs are re-derived by tests.
- **Fresh copy** (deep 220-character path, no `.git`, no FLORES text): **139 passed, 57 skipped, 0 failed**. Each skip names its fix (`prep.py`; the Llama licence plus `hf auth login`).

## Git (local only; no pushes; `origin` configured but untouched)
- **`main`:** `48f28fe` (A1 merged). `part-a-corpus` = `9192110` (merged, kept).
- **`part-a-audit`:** 38 commits on top of `main`, all authored by `anujsh2004` only, with 0 attribution lines.
  - Pre-registration and reproduction: `3a5f83d`, `fadbc4d`, `46b3921`, `ae95181`.
  - F1: `e542deb` `22cf99f` `854a763`. Evaluation round: `19aee1b` `ded8448` `be9454c` `2532cea` `59bdddc` `39f7e25`.
  - F3: `b59dd6f` `4afb3fd` `9801958`. F4: `24f478f` `cd79142` `07baf4d`. F2: `bbc2603` `d5c6ccb` `6c149ec`. F5: `df082a8`. F6: `f0bc984` `95f030c` `a58fd0a`. F7/F8: `77736a1` `a09ca93`.
  - F9: `8737bc3` `e7bc8f9` `31c0bda`. Ablation, report, audit: `5a6cecf` `26cc397` `61cd46b`. Mutation and docs: `ac35128` `b995990`. Portability: `0e88633`. This state update is the final commit.
- **Dates:** author dates = newest file time in each commit (user's choice); commit dates = real commit times.

## What is not in git
- FLORES sentence text and metadata (D-11; `prep.py` regenerates them).
- `partA/corpus/raw/`, `.venv/`, caches, the HF cache.
- `AI_USAGE.md`: deleted at the user's request. **The assignment requires it**, and the user has been told.

## Decisions
- **Decided:** D-01 (ack pending), D-02, D-03, D-04 (pins and hashes), D-05, D-08, D-10, D-11, D-12, D-13, D-14 (+ amendment 1), D-15, D-17.
- **User-confirmed 2026-10-22:** D-14 amendment 2 (post-hoc conclusion rule) and D-16 (V1 sentence denominator).
- **Provisional:** D-06, the single cost number, for A3.
- **Open:** D-07 (Part C), D-09 (B1 GB vs GiB).

## Environment facts (checked)
- **Venv:** `.venv` on Python 3.14.0 with pytest 9.1.1, regex 2026.9.29, tiktoken 0.14.0, tokenizers 0.23.3, transformers 5.20.2, numpy 2.5.4, pandas 3.0.6. No torch.
- **Tokenizers (pinned):** gpt2 (tiktoken); `FacebookAI/xlm-roberta-base@e73636d4`; `meta-llama/Llama-3.2-3B@13afe512` (gated; access granted to anujsh2004; `tokenizer.json` SHA-256 `79e3e522…b2b4`).
- **Git:** `core.autocrlf=true`; overridden by `.gitattributes`.
- **Windows MAX_PATH:** repo paths are capped at 80 characters by a test.

## User answers (2026-10-22)
1. Merge approved; done as a `--no-ff` merge into `main` (see the git log).
2. D-14 amendment 2 accepted.
3. D-16 confirmed.
4. `AI_USAGE.md` will be written at the end (Phase 7).

Still open: D-01 layout acknowledgement.

## Next steps
A3 on `part-a-analysis`:
1. Bootstrap CIs on the per-sentence ratios (≥2 tokenizers; reuse `units.cluster_bootstrap_ratio`).
2. Decide the single routing/cost number (D-06), including per-request overhead and output tokens.
3. Then A4's memo, then Part B.
