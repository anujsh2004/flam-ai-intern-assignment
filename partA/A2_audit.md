# A2 — Audit of `fertility.py` and REPORT_v0 §1

Every number below carries an evidence ID `[E#]`. The **Evidence index** at the end maps each ID to the exact JSON file and field it came from. A test (`partA/tests/test_audit_evidence.py`) checks every index entry against that JSON, so a number here cannot drift from the measurement. The full measured tables are in [`A2_results.md`](A2_results.md), which is generated, never hand-typed.

## Summary

| # | Where (`starter_kit/fertility.py`) | Type | Verdict | Headline effect |
|---|---|---|---|---|
| F1 | L62 `line.split(" ")` | Code bug | **Material** | Double spaces add empty "words": FLORES kan fertility understated by 2.78% [E1] |
| F2 | L64–67 mean of per-line ratios | Method / decision flaw | **Material** | Short lines over-weighted: kan fertility overstated by 1.61% (gpt2) / 1.70% (XLM-R) [E13, E14] |
| F3 | L60 `.lower()` | Code bug | **Material** | Measures text that is never served. English inflated, so the hin/eng ratio is understated by 3.57% (gpt2) / 1.73% (XLM-R) [E6, E7] |
| F4 | L49 NFC | **Looks suspicious but fine** | Negligible | Largest effect −0.11% [E9] |
| F5 | L21, L25 `random` / `seed(1337)` | Technical debt | No effect (proven) | `random` is used only in its import and seed. Removed in v1. |
| F6 | L33 `add_special_tokens=False` | **Looks suspicious but fine** | Correct as written | Flipping it would inflate fertility by up to 23.74% on short lines [E18] |
| F7 | Tokens per *word* as the cost metric | **Conceptual flaw** | **Material** | Per word vs per parallel sentence, FLORES gpt2 ratio: hin 6.10 → 7.18, kan 17.40 → 13.11 [E20–E23] |
| F8 | `len(line)` as "char"; "tok/char confirms" | **Conceptual flaw** | **Material** | Same tokens: hin per-"char" premium is 2.77× to 10.89× depending only on the unit [E25, E26] |
| F9 | `gpt2` as the instrument | **Conceptual flaw** (the cost is our model's) | **Material, largest** | With the FLM-4B proxy tokenizer, hin per-sentence ratio is 7.44 → 2.53 (−66.0%) [E34–E35, E39] |

**Bottom line for leadership.** The report's arithmetic is faithful to its code: the unmodified script reproduces 5.887 [E31]. But the number answers the wrong question with the wrong instrument:
- Measured per parallel sentence, so the same content is compared, and with a tokenizer from the serving model's family (Llama-3), Hindi costs about **2.5×** English on FLORES [E35], not about 6×.
- Kannada costs **8.87×** and Tamil **7.63×** [E36, E37]. These remain large.

## Method (how every claim was tested)

1. **Reproduce first.** `audit/v0.py` loads the original only if its SHA-256 matches the provided file. The CLI reproduces "hin is 5.89x" exactly (`tests/test_v0_reproduction.py`).
2. **One flag per fix.** `partA/fertility_v1.py --v0` matches the original's output byte-for-byte on the toy corpus and all 8 FLORES files. Each fix is one `Config` field and CLI flag, so `--v0 --split whitespace` isolates F1.
3. **Pre-registered before any measurement** (D-13, D-14): the verdict per finding, and the threshold "negligible = |Δ| < 1% on every reported metric".
   - The second half of D-14, "the report's conclusion is unchanged", is defined **post-hoc**, after seeing all metrics, as the user decided. It is applied in the conclusions section and labelled there.
4. **Corpora and instruments.**
   - Corpora: the toy corpus (what the report used) and FLORES-200, 2,009 parallel sentences × eng/hin/kan/tam (A1).
   - Tokenizers: gpt2 (the report's); XLM-R (pinned `e73636d4`); and Llama-3.2-3B (pinned `13afe512`), the FLM-4B proxy whose config matches `model_spec.md` on all 5 architecture numbers (D-04).
5. **Quality of the evidence.**
   - Fake-tokenizer unit tests with hand-derived values.
   - An independent recompute of F1 using no project code (max difference 0).
   - Committed results equal a fresh recompute (staleness tests).
   - A mutation check (`audit/mutation_check.py`): every planted bug is killed.

Reproduce everything:
```
python partA/corpus/prep.py                      # FLORES text (not committed, D-11)
python partA/audit/experiments.py F1 --tokenizer gpt2     # any finding/tokenizer; F9: --config v0|v1
python partA/audit/ablation.py && python partA/audit/report.py
python -m pytest partA/tests                     # includes staleness tests for every number
python partA/audit/mutation_check.py
```

## Findings

### F1 — `line.split(" ")` counts empty words (code bug)
- **Claim:** a double space makes `split(" ")` return `""`, which is counted as a word. That inflates the denominator.
- **Experiment:** `python partA/audit/experiments.py F1 --tokenizer gpt2` (v0 vs v0 + `split=whitespace`).
- **Before → after:** toy hin fertility +2.01% [E3]; the report's ratio 5.887 → 5.922 [E31, E4]. FLORES kan **+2.78%** [E1], on 507 of 2,009 lines whose *word* count changed [E2].
- **Why the delta proves it:** only the word count changes (token-line count = 0), and every changed line contains a double ASCII space and no other whitespace. So the shift is caused purely by empty "words".
- **Direction:** v0 *understates* fertility. The blast radius was pre-registered as "small"; after measurement it was revised to material (user-accepted, D-13).

### F2 — mean of per-line ratios (method / decision flaw)
- **Claim:** averaging per-line ratios gives a 3-word line the same weight as a 40-word line, so the metric depends on where line breaks fall. The cost of a text is total tokens ÷ total units.
- **Experiment:** `python partA/audit/experiments.py F2` (`aggregate=total`).
  - Constructed test corpus: per-line mean 3.0 vs totals 24/15 = 1.6.
  - Re-splitting one line moves the mean but not the totals.
- **Before → after:** FLORES kan **−1.61%** (gpt2) [E13], **−1.70%** (XLM-R) [E14]. The hin/eng ratio moves only +0.24% [E15], because the bias partly cancels across languages.
- **Why the delta proves it:** no line's own value changes (0 changed lines). The whole delta comes from how lines are weighted.
- **Direction:** v0 *overstates* fertility, in 11 of 12 language × tokenizer cells.

### F3 — `.lower()` measures text that is never served (code bug)
- **Claim:** the model tokenizes the text as served, which is cased. Lowercasing changes only Latin-script tokens, so it biases the English baseline and therefore every ratio.
- **Experiment:** `python partA/audit/experiments.py F3 --tokenizer gpt2` and `--tokenizer hf:FacebookAI/xlm-roberta-base@e73636d4…`.
- **Before → after:** FLORES eng fertility **−3.45%** when cased [E5], on 925 lines with token changes [E8]. hin/eng ratio **+3.57%** (gpt2) [E6] and +1.73% (XLM-R) [E7]. Indic fertility moves under 0.05%.
- **Why the delta proves it:** the effect falls almost entirely on English, the only cased script. Lowercased English needs *more* tokens, so v0 *understates* the Indic gap.

### F4 — NFC normalisation (looks suspicious but fine)
- **Claim tested:** NFC changes about 9% of Hindi FLORES lines (precomposed nukta letters, A1). Does that distort the result?
- **Experiment:** `python partA/audit/experiments.py F4` under gpt2 and XLM-R.
- **Result:** the largest effect is −0.11% (gpt2 hin) [E9] and +0.06% (XLM-R kan) [E10]. Under XLM-R, tokens change on only 3 Hindi lines [E11], while 183 lines change some metric [E12]. Its normaliser absorbs the nukta, so those 183 lines move only tok/char's code-point denominator.
- **Verdict:** negligible under D-14 for both tokenizers. Keeping NFC is fine.

### F5 — unused `random.seed(1337)` (technical debt)
- **Evidence:**
  - The AST shows `random` used only in its `import` and `.seed` (`tests/test_f5_seed.py`).
  - v0's numbers are identical after perturbing the global RNG with three different seeds.
  - v1 does not import `random`.
- **Verdict:** no effect. Removed as debt. Mutants that reintroduce it are caught.

### F6 — `add_special_tokens=False` (looks suspicious but fine)
- **Claim tested:** would counting special tokens be the "right" fertility, or a false inflation?
- **Experiment:** `python partA/audit/experiments.py F6` with `--special-tokens`.
  - Special tokens are modelled as a per-sequence count.
  - That count was verified against XLM-R's own `add_special_tokens=True` output on 400 FLORES lines.
- **Result:** gpt2 exactly 0 (tiktoken adds none) [E16]. With XLM-R, counting `<s></s>` per line inflates FLORES eng by **+7.35%** [E17] and toy hin by **+23.74%** [E18], and pulls the hin ratio down 1.24% [E19].
- **Verdict:** v0's `False` is correct for a per-text metric. Flipping it would be false fertility, worse on short lines. Requests pay special tokens once each; that is A3's cost model, not fertility.

### F7 — tokens per *word* is not a cost ratio (conceptual flaw)
- **Claim:** the code correctly computes tokens ÷ whitespace words, but words do not hold content constant across languages. The same FLORES sentences take 1.17× English's words in Hindi but 0.74× in Kannada (A1). A ratio of fertilities is therefore not a ratio of costs.
- **Experiment:** `python partA/audit/experiments.py F7` (`denominator=sentence`), the same tokens per parallel sentence.
- **Before → after (ratio vs eng, FLORES, gpt2):** hin **6.10 → 7.18** [E20, E21]; kan **17.40 → 13.11** (−24.64%) [E23, E22, E24]. XLM-R shows the same shifts (`A2_results.md` §1).
- **Why the delta proves it:** the tokens are identical, so the shift is caused only by the denominator.
  - The ablation confirms this analytically. F7's contribution for kan is −26.43% under gpt2 [E42], and the same under XLM-R and Llama (`A2_results.md` §2). That equals 31,530/42,855 − 1, the kan/eng word ratio [E44, E45].
  - So the denominator, not the tokenizer, produces this distortion.
- **Direction:** per-word ratios understate Hindi's cost and overstate Kannada's and Tamil's.

### F8 — "tok/char confirms" is not independent (conceptual flaw)
- **Claim:** code points mean different things in different scripts. Also, fertility and tok/char share the numerator, so their "agreement" is not a second measurement.
- **Experiment:** `python partA/audit/experiments.py F8_graphemes` and `F8_bytes`.
- **Result (same tokens, hin tok/char ratio vs eng, FLORES gpt2):** per code point 7.12 [E27], per grapheme **10.89** [E25], per UTF-8 byte **2.77** [E26]. Per byte under XLM-R it is **0.48** [E28]: Hindi looks *cheaper* than English.
- **The report's "agreement":** our reproduction gives 5.887 per word [E31] vs 6.998 per char [E29]. Both are tokens divided by different unit counts. Their ratio is just the characters-per-word ratio, not confirmation.

### F9 — GPT-2 is not our model's tokenizer (conceptual flaw)
- **Claim:** leadership's cost is FLM-4B's tokens. gpt2's vocabulary is English-centric and is not the serving tokenizer.
- **By the user's rule** (GPT-2 cost → validity flaw; our model's cost → conceptual flaw): the report says "cost **us**", so this is a conceptual flaw.
- **Experiment:** `python partA/audit/experiments.py F9 --config v0` and `--config v1`. Config fixed; gpt2 swapped for Llama-3.2-3B (proxy, D-04).
- **Result:**
  - v0 metric, toy hin: **5.89 → 2.08** [E31, E32].
  - V1, FLORES hin per sentence: **7.44 → 2.53 (−66.0%)** [E34, E35, E39].
  - English's own V1 value moves only +0.34% [E30].
- **Why the delta proves it:** same script, same sentences, same config. Only the tokenizer changed, and the Hindi premium fell by about 3×.
- **Caveat:** a proxy, not FLM-4B itself. The parameter count differs (4.2B vs ~3.2B).

## Interactions (ablation, `A2_results.md` §2–3)

- **F7 subsumes F1 and F2.** In V1, which divides by sentences, removing F1 or F2 changes tokens per sentence by exactly 0.00% under all three tokenizers.
  - Word splitting is unused, and each line's denominator is 1, so the per-line mean equals the total ÷ the line count.
  - They are real flaws in v0's per-word metric, but the conceptual fix makes them moot. F2 still moves tok/char by 0.5–1.1%.
- **F3 survives in V1:** removing it changes the hin ratio by +3.60% (gpt2), +1.76% (XLM-R), +1.92% (Llama) [E43].
- **F9 is the largest single effect;** F7 is second.

## REPORT_v0 §1 claims, audited

| Report claim | Verdict | Evidence |
|---|---|---|
| "Hindi fertility is **5.89×** worse than English" | **True as computed** by its code (5.887) | [E31] |
| "Serving Hindi will cost us roughly **6×** more per request" | **Not supported.** It measures per word (F7) with gpt2 (F9). With the FLM-4B proxy, per parallel sentence on FLORES, Hindi is ≈ **2.53×**. | [E35] |
| "tok/char 1.579 vs 0.226 = 7.0× **confirms** the per-word number" | **Refuted as evidence.** It shares the numerator. Changing only the character unit moves it from 2.77× to 10.89×. | [E26, E25, F8] |
| "Hindi simply has **more Unicode characters per word**" | **False on our data.** FLORES hin has 5.10 code points per word vs eng 6.00. | [E40, E41, E46, E47] |
| "This is a property of the script, not the tokenizer" | **Refuted.** Same Devanagari text: gpt2 7.44× vs Llama proxy 2.53× vs XLM-R 1.25× per sentence. | [E34, E35, `A2_results.md` §2] |
| "No further measurement needed — the two metrics agree, so the result is robust" | **Refuted.** The agreement is an artefact (F8), and the result moves about 3× with the instrument (F9). | F8, F9 |
| "Route all Indic traffic to a separate Indic tokenizer/model; budget 6× for Hindi" | **Premise invalid.** The 6× budget is not supported. The routing decision is re-made in A3/A4 on the corrected metric. | — |

## Conclusion-level verdicts (D-14 second half, defined post-hoc)

**Post-hoc rule** (defined after all metrics were seen, as the user decided): a fix "changes the conclusion" if it changes the report's Hindi multiplier at its own precision (≈6×, rounded to the nearest integer), or breaks the "metrics agree" or "property of the script" claims. Under this rule:
- **F7, F8 and F9 change the conclusions.**
- **F1, F2, F3, F4, F5 and F6 do not.** F3 moves FLORES gpt2 hin from 6.10 to 6.32 [E6], which is still about 6×.

This rule is disclosed as post-hoc and awaits user confirmation.

## Limitations

- **Proxy, not ground truth:** F9 uses a Llama-3.2-3B proxy; FLM-4B's actual tokenizer is not available.
- **Domain:** FLORES is formal, English-sourced text (A1 limitations). Chat, code-mixed and romanised traffic is untested.
- **Point estimates only:** no confidence intervals on token ratios here. A3 adds bootstrap CIs.
- **Cost model:** per-request overhead (BOS/special tokens, F6) and output tokens are A3/A4 questions, not fertility.

## Evidence index

Each row: ID | file | JSON path | value as quoted above. Verified by `partA/tests/test_audit_evidence.py`.

| ID | file | path | value |
|---|---|---|---|
| E1 | partA/audit/results/F1_gpt2.json | delta_pct.flores.kan.fertility | +2.78% |
| E2 | partA/audit/results/F1_gpt2.json | lines_changed.flores.kan.words | 507 |
| E3 | partA/audit/results/F1_gpt2.json | delta_pct.toy.hin.fertility | +2.01% |
| E4 | partA/audit/results/F1_gpt2.json | after.toy.hin.fertility_ratio_vs_eng | 5.922 |
| E5 | partA/audit/results/F3_gpt2.json | delta_pct.flores.eng.fertility | -3.45% |
| E6 | partA/audit/results/F3_gpt2.json | delta_pct.flores.hin.fertility_ratio_vs_eng | +3.57% |
| E7 | partA/audit/results/F3_xlmr.json | delta_pct.flores.hin.fertility_ratio_vs_eng | +1.73% |
| E8 | partA/audit/results/F3_gpt2.json | lines_changed.flores.eng.tokens | 925 |
| E9 | partA/audit/results/F4_gpt2.json | delta_pct.flores.hin.fertility | -0.11% |
| E10 | partA/audit/results/F4_xlmr.json | delta_pct.flores.kan.fertility | +0.06% |
| E11 | partA/audit/results/F4_xlmr.json | lines_changed.flores.hin.tokens | 3 |
| E12 | partA/audit/results/F4_xlmr.json | lines_changed.flores.hin.any_metric | 183 |
| E13 | partA/audit/results/F2_gpt2.json | delta_pct.flores.kan.fertility | -1.61% |
| E14 | partA/audit/results/F2_xlmr.json | delta_pct.flores.kan.fertility | -1.70% |
| E15 | partA/audit/results/F2_gpt2.json | delta_pct.flores.hin.fertility_ratio_vs_eng | +0.24% |
| E16 | partA/audit/results/F6_gpt2.json | delta_pct.flores.hin.fertility | +0.00% |
| E17 | partA/audit/results/F6_xlmr.json | delta_pct.flores.eng.fertility | +7.35% |
| E18 | partA/audit/results/F6_xlmr.json | delta_pct.toy.hin.fertility | +23.74% |
| E19 | partA/audit/results/F6_xlmr.json | delta_pct.flores.hin.fertility_ratio_vs_eng | -1.24% |
| E20 | partA/audit/results/F7_gpt2.json | before.flores.hin.fertility_ratio_vs_eng | 6.10 |
| E21 | partA/audit/results/F7_gpt2.json | after.flores.hin.fertility_ratio_vs_eng | 7.18 |
| E22 | partA/audit/results/F7_gpt2.json | after.flores.kan.fertility_ratio_vs_eng | 13.11 |
| E23 | partA/audit/results/F7_gpt2.json | before.flores.kan.fertility_ratio_vs_eng | 17.40 |
| E24 | partA/audit/results/F7_gpt2.json | delta_pct.flores.kan.fertility_ratio_vs_eng | -24.64% |
| E25 | partA/audit/results/F8_graphemes_gpt2.json | after.flores.hin.tok_per_char_ratio_vs_eng | 10.89 |
| E26 | partA/audit/results/F8_bytes_gpt2.json | after.flores.hin.tok_per_char_ratio_vs_eng | 2.77 |
| E27 | partA/audit/results/F8_bytes_gpt2.json | before.flores.hin.tok_per_char_ratio_vs_eng | 7.12 |
| E28 | partA/audit/results/F8_bytes_xlmr.json | after.flores.hin.tok_per_char_ratio_vs_eng | 0.48 |
| E29 | partA/audit/results/F8_bytes_gpt2.json | before.toy.hin.tok_per_char_ratio_vs_eng | 6.998 |
| E30 | partA/audit/results/F9_v1.json | delta_pct.flores.eng.fertility | +0.34% |
| E31 | partA/audit/results/F8_bytes_gpt2.json | before.toy.hin.fertility_ratio_vs_eng | 5.887 |
| E32 | partA/audit/results/F9_v0.json | b.toy.hin.fertility_ratio_vs_eng | 2.08 |
| E33 | partA/audit/results/F9_v0.json | b.flores.hin.fertility_ratio_vs_eng | 2.11 |
| E34 | partA/audit/results/F9_v1.json | a.flores.hin.fertility_ratio_vs_eng | 7.44 |
| E35 | partA/audit/results/F9_v1.json | b.flores.hin.fertility_ratio_vs_eng | 2.53 |
| E36 | partA/audit/results/F9_v1.json | b.flores.kan.fertility_ratio_vs_eng | 8.87 |
| E37 | partA/audit/results/F9_v1.json | b.flores.tam.fertility_ratio_vs_eng | 7.63 |
| E39 | partA/audit/results/F9_v1.json | delta_pct.flores.hin.fertility_ratio_vs_eng | -66.0% |
| E40 | partA/corpus/stats.json | languages.hin_Deva.codepoints | 256462 |
| E41 | partA/corpus/stats.json | languages.hin_Deva.words | 50250 |
| E42 | partA/audit/ablation.json | by_tokenizer.gpt2.leave_one_out.F7.delta_pct_v1_vs_without.flores.kan.fertility_ratio_vs_eng | -26.43% |
| E43 | partA/audit/ablation.json | by_tokenizer.gpt2.leave_one_out.F3.delta_pct_v1_vs_without.flores.hin.fertility_ratio_vs_eng | +3.60% |
| E44 | partA/corpus/stats.json | languages.kan_Knda.words | 31530 |
| E45 | partA/corpus/stats.json | languages.eng_Latn.words | 42855 |
| E46 | partA/corpus/stats.json | languages.eng_Latn.codepoints | 257160 |
| E47 | partA/corpus/stats.json | languages.eng_Latn.words | 42855 |
