# Decision log

Format per decision: problem, alternatives (pros/cons), assumptions & constraints, evaluation criteria & evidence, choice and rationale, why alternatives were rejected, when another would win, status.
Statuses: **Decided** (evidence in hand), **Provisional** (reasoned, awaiting experiment), **Open**.
Sources must be real and read; none are cited yet. Where X/Twitter or articles are used they are supplementary, never proof.

---

## D-01 Repository layout and branch strategy — Decided (needs user ack)
- **Problem:** how to organise the repo so it matches the required deliverable and stays reviewable.
- **Alternatives:** (1) repo root = submission root with `partA/ partB/ partC/`, docs under `docs/`; (2) nested `your-submission/` folder; (3) docs at root.
- **Pros/cons:** (1) matches the PDF tree and graders open the repo directly; fewer path surprises. (2) literal to the PDF text but adds a pointless level. (3) clutters the root.
- **Assumptions:** the PDF's `your-submission/` is a placeholder name for the repo root.
- **Choice:** option 1. Branch-per-phase off `main`, `--no-ff` merges after tests pass.
- **Rejected:** 2 (redundant nesting). **When others win:** if graders require the literal folder name — trivial to rename.
- **Open question for user:** confirm.

## D-02 Language/tooling for analysis — Decided
- **Problem:** implementation language/test tooling.
- **Alternatives:** Python + pytest; Python + unittest; notebooks.
- **Evidence/constraints:** starter code is Python; installed: Python 3.14, numpy, pandas, matplotlib. `pytest`, `tiktoken`, `transformers` not installed (checked via pip list).
- **Choice:** Python scripts + pytest (BDD scenarios written as Given/When/Then docstrings/test names; `pytest-bdd` is not needed — avoids dependency weight). Notebooks rejected: poor diffs, hard for a live defense edit.
- **Risk:** Python 3.14 may lack wheels for some libs (tiktoken/tokenizers/torch). Fallback is a Python 3.11/3.12 venv.
- **Verified 2026-10-21:** a 3.14 venv installs and imports pytest 9.1.1, regex 2026.9.29, tiktoken 0.14.0, tokenizers 0.23.3 and transformers 5.20.2. PyTorch is not installed, which is fine: tokenizers only. Status: **Decided.**

## D-03 Evaluation corpus source (A1) — Decided (verified 2026-10-21)
- **Problem:** A1 needs >=4 languages (English, Hindi, 2 Dravidian) to measure tokenizer cost across languages. The A3 question ("what should the denominator hold constant?") needs text whose *content* is the same across languages.
- **Criteria (priority order):**
  1. parallel by construction, so content is held constant;
  2. covers eng/hin and >=2 Dravidian languages;
  3. translation quality and documented provenance;
  4. comparability with published tokenizer studies;
  5. reproducible access without credentials;
  6. licence permits our use;
  7. size enough for stable corpus-level ratios.

  Domain match to production traffic is wanted, but no candidate fully meets it, so it is handled as a caveat.

| Candidate | Parallel? | Provenance / quality | Size | Access, licence | Main weakness |
|---|---|---|---|---|---|
| **FLORES-200 dev+devtest** (chosen) | N-way, line-aligned; 200 langs incl. hin/kan/tam/tel/mal | Professional translation from English, QA threshold 90/100 (Goyal et al.) | 997+1,012 | Ungated tarball (hash-checked); CC BY-SA 4.0 | Formal Wiki register; translationese (English-original) |
| FLORES+ (OLDI) | Same text, 230 langs | FLORES-200 plus maintained corrections | Same | HF gated + token; CC BY-SA 4.0; asks no training use and no public redistribution | Needs credentials; less used in published fertility tables |
| IN22-Gen (AI4Bharat) | N-way, 22 Indic + English | India-centric Wiki/Web content | 1,024 | HF; CC BY 4.0 | Less standard for fertility comparisons |
| IN22-Conv | N-way | Conversational-style sentences | 1,503 | HF; CC BY 4.0 | Small; still translated |
| Samanantar | Pairwise en-X, mined | Automatically mined, noisy | very large | Download | Not an eval set; not N-way; misalignment noise |
| Tatoeba | Partly | Volunteer, very short sentences | Uneven | CC BY | Uneven coverage, short, not N-way |
| Self-assembled (e.g. per-language Wikipedia) | No | Not parallel | Any | Varies | Content not constant, so cross-language ratios are uninterpretable |

- **Evidence (all checked this session):**
  - **Access:** tarball HTTP 200, 25,585,843 bytes, SHA-256 `b8b0…11f6`.
  - **Splits:** 997/1,012 lines in all 4 languages; 281+281 articles, matching FLORES-101 Table 1.
  - **Alignment:** number-match 99.2–99.7%; length ratio range 0.49–2.03.
  - **Duplicates and register:** 0 duplicates; wikinews/wikibooks/wikivoyage 689/652/668.
  - **Licence:** CC BY-SA 4.0 per the HF card.
  - **Comparability:** Petrov et al. (NeurIPS 2023, §3–4) define the premium |t(s_A)|/|t(s_B)| on FLORES-200's ~2,000 sentences, the same unit we use.
  - **Provenance:** FLORES-101 (Goyal et al., ar5iv §3) describes 3–5 contiguous sentences per article, translation from English and the 90% quality threshold.
  - **Sample size:** codepoint-ratio CI is about ±0.7%. The article-clustered and i.i.d. CIs are nearly equal, and dev vs devtest agree within 0.8%.
- **Why chosen:** it is the only candidate that meets criteria 1–6 together. It is parallel and professionally translated, so a per-sentence comparison holds content constant. It is the standard set in tokenizer-parity work, so our numbers can be checked against the literature. It needs no credentials, which matters for a reproducible repo and the live defense.
- **Why not the others:**
  - **FLORES+:** same text but needs credentials. It is the right choice if language-specific corrections matter.
  - **IN22-Gen:** a better domain match for India-centric topics. It would be the stronger primary corpus if the question were Indian-origin content rather than "same content vs English". A good robustness check.
  - **IN22-Conv:** closest to chat register. It would serve best for estimating casual-traffic cost; future work.
  - **Samanantar and Tatoeba:** fail the parallel or quality criteria.
- **When another would win:** if production traffic is conversational or India-centric, IN22-Conv or IN22-Gen numbers would be more predictive of real cost.
- **Splits:** dev + devtest (2,009). No training happens, so there is no leakage reason to hold devtest out. Splits are reported separately as a consistency check.
- **Status:** **Decided.**

## D-04 Tokenizers for A2/A3 — Decided for A2 (2026-10-21); A3 may add more
- **A2 set:**
  - `gpt2` (tiktoken): the original instrument, held fixed to isolate script flaws.
  - `xlm-roberta-base`: open, ungated, multilingual SentencePiece. Used for F3/F4 because whether lowercasing or NFC matters depends on the tokenizer's own normalisation.
  - **Llama-3.2-3B tokenizer** (vocab 128,256): proxy for FLM-4B's tokenizer.
- **Why Llama-3.2-3B is the FLM-4B proxy (evidence):**
  - **Config match:** its `config.json` (read from the ungated mirror `unsloth/Llama-3.2-3B`) matches `model_spec.md` on every architecture number: 28 layers, d_model 3072, 24 Q heads, 8 KV heads, head_dim 128, vocab 128,256 ≈ "128k".
  - **Mismatch:** parameter count, ~3.2B (tied embeddings) vs 4.2B. So FLM-4B is *not* literally this model, and the tokenizer is a proxy, not ground truth.
  - **Language support:** Hindi is officially supported per the model card.
- **Alternatives near 128k:**
  - Mistral-Nemo Tekken: 131,072 (Salamandra report).
  - DeepSeek-V3: ~128.8k–129.3k, sources disagree.

  Vocab sizes are close, but neither matches the architecture. Gemma (~256k) and Qwen (~152k) are further away.
- **Access:** the official `meta-llama/Llama-3.2-3B` repo is gated. **Granted 2026-10-21 (user).**
  - **Pinned revision:** `13afe5124825b4f3751f836b40dafda64c1ed062`.
  - **Official `config.json`:** matches all 5 spec numbers; vocab 128,256; tied embeddings.
  - **`tokenizer.json` SHA-256:** `79e3e522635f3171300913bb421464a87de6222182a0570b9b2ccba2a964b2b4`.
  - Adds 1 special token (BOS).
  - The planned mirror hash-check was dropped, since the official file is used directly.
- **Other pins:** XLM-R `FacebookAI/xlm-roberta-base@e73636d4f797dec63c3081bb6ed5c7b0bb3f2089`; vocab 250,002; ungated; case-sensitive; precompiled normaliser.
- **Earlier option list (kept for the record):** baseline `gpt2`/tiktoken (as v0); `cl100k_base`/`o200k_base`; XLM-RoBERTa (SentencePiece, multilingual); an Indic-focused tokenizer (e.g. IndicBERT/MuRIL); Llama-3 / Gemma / Qwen tokenizers (open weights).

## D-04a (superseded) original D-04 notes
- **Alternatives:** baseline `gpt2`/tiktoken (as v0); `cl100k_base`/`o200k_base`; XLM-RoBERTa (SentencePiece, multilingual); an Indic-focused tokenizer (e.g. IndicBERT/MuRIL); Llama-3 / Gemma / Qwen tokenizers (open weights).
- **Criteria:** open and downloadable without gating, Indic coverage, relevance to a ~128k-vocab model like FLM-4B (spec says 128k vocab — Llama-3-class tokenizer is the closest comparison), ease of reproduction.
- **To verify:** which load offline-reproducibly; effect of vocab size on fertility (confounded by vocab — must note in caveats).
- **Status:** Superseded by D-04 above (2026-10-21). Kept for history.

## D-05 Grapheme-cluster counting (A3 denominator) — Decided, with a documented non-uniformity
- **Alternatives:** `regex` `\X` (UAX #29 extended grapheme clusters); `grapheme` package; manual count of non-combining code points; ICU (PyICU, a heavy Windows install).
- **Evidence (`partA/tests/test_units.py`; Python unidata 16.0.0, regex 2026.9.29):**
  - **Vowel signs and combining marks:** attach correctly. हि = 1 cluster, and "cafe" + U+0301 = 4 clusters.
  - **Devanagari, Telugu and Malayalam conjuncts:** ka+virama+ssa forms **1** cluster, and नमस्ते is 3 clusters. This is the Unicode 15.1 conjunct rule.
  - **Kannada and Tamil conjuncts:** the same sequence gives **2** clusters.
- **Implication:** grapheme clusters are **not a uniform unit across our languages**. Relative to Hindi, they over-count Kannada conjuncts. For Tamil the split matches the visible pulli, so it is arguably correct there.
- **Decision:** use `regex` `\X` for the grapheme column. It is standard, already a dependency and pinned by tests. Do **not** use graphemes as the deciding denominator; carry this caveat wherever the column appears.
- **When another would win:** a script-aware akshara (syllable) segmenter would give a uniform visual unit. It is not worth the complexity, because the deciding denominator is the parallel sentence (D-06).
- **Status:** Decided.

## D-06 Which single number drives routing/cost (A3) — Provisional (hypothesis)
- **Reasoning so far:** a denominator should hold *content/meaning* constant across languages. Whitespace words and UTF-8 bytes do not (word boundaries and script byte widths differ by language). On parallel text, tokens per parallel sentence (or tokens relative to the English token count for the same sentence) holds content approximately constant, and is what billing/context cost actually tracks.
- **Caveat:** translations differ in length/information; cost depends on both input and output token counts; per-sentence average is sensitive to sentence length mix.
- **A1 evidence (denominators only, no tokenizer yet):**
  - **Words:** the same content takes 1.17× English whitespace words in Hindi, but 0.74× in Kannada and 0.77× in Tamil.
  - **Bytes:** 2.56–3.19×.
  - **Code points:** 1.00–1.17×.
  - **Conclusion:** word and byte denominators distort in different directions for identical content, which supports holding content constant via parallel sentences.
- **Needs:** experiment with real tokenizers; compare ratios under each denominator. Status: **Provisional — not to be stated as a result.**

## D-07 Part C approach (SFT vs rewriter vs prompting) — Open
- **Constraints:** 1xA100-80GB for 2 wks; reviewer only for Hindi+Kannada, 10 h/wk (=20 h in the GPU window); launch review in 3 wks; no external API.
- **Considerations to quantify:** SFT data volume vs reviewer verification capacity; rewriter adds latency per request and 6-language quality with no native check for 4 languages; prompting is cheapest and sets the baseline that SFT/rewriter must beat.
- **Process:** decide after Phase 1-5 with numeric arithmetic; the day-1 experiment likely is a prompt-only baseline measured by the reviewer. Status: **Open.**

## D-08 Authorship and attribution — Decided (user instruction)
- User is the sole author on GitHub. No `Co-Authored-By` or tool-attribution lines in commits/PRs/files. Existing global git identity (`anujsh2004`) is used unchanged.

## D-09 GB vs GiB and budget formula for B1 — Open
- `gpu_memory_utilization` 0.92 of 24 GB; weights 4.2B x 2 B; overhead 1.6 GB. Whether "24 GB" means 24e9 or 24 GiB changes the sequence count by ~1; answer must state the convention and show both. Check against the log (`preempted_seqs` begins at batch 32; `kv_cache_util` 0.93 at batch 24). Status: **Open — resolve in Phase 5 (Part B) with tests.**

## D-10 Work order: Part A before B and C — Decided (user recommendation)
- **Alternatives:** B first (small, deterministic) vs A first.
- **Reasoning:** B and C depend only on `bench/` and the prompt; A1->A3 is the longest chain and carries network/library-install risk, and is 50 of 100 points. Cost: B's cheap points come later. Order: A1, A2 (may start on toy corpus in parallel), A3, A4, B, C.
- **Python:** try a Python 3.14 venv first; fall back to 3.12 if tokenizer wheels are missing (D-02).

## D-11 Redistribution of FLORES text in the repo — Decided: option (b), not committed for now (user, 2026-10-21)
- **Problem:** we earlier agreed to commit the prepared text so the repo runs offline. Research since then turned up two things:
  - **FLORES+ card:** asks that the data not be used for training and not be redistributed publicly unless it is protected from scraping.
  - **`facebook/flores` card:** gates access under the heading "Protecting the integrity of FLORES for evaluation". The gated conditions themselves can't be read without logging in.
- **Alternatives:**
  - **(a) Commit the text:** offline and simple, but it puts eval text in a public, scrapeable GitHub repo, against the integrity request.
  - **(b) Commit scripts, manifest and aggregate `stats.json` only:** `prep.py` regenerates the text, hash-verified, with one command and one ~26 MB download.
  - **(c) Commit an encrypted or zipped copy:** extra complexity with no benefit over (b).
- **Proposed:** (b). Reproducibility is unchanged because the download is scripted and hash-checked, and the evaluation set's integrity is respected.
- **When (a) would win:** a private repo, or a grader without network access. The ZIP submission option could include the text then.
- **Status:** **Decided (b) "for now"** by the user on 2026-10-21. Enforced by `.gitignore` (`partA/corpus/prepared/*.txt`, `*.tsv`); `manifest.json` stays tracked. Revisit if the submission goes out as a ZIP.

## D-12 Line endings and dependency pins — Decided (2026-10-21)
- **Line endings:**
  - **Problem:** this machine has `core.autocrlf=true`, and on Windows Python's `write_text` emits `\r\n`. A2 audits the starter kit's exact bytes (e.g. double spaces), so conversions must be impossible.
  - **Decision:** `.gitattributes` with LF for authored text, `-text -eol` for `starter_kit/**` and the FLORES text, and `binary` for archives and documents. Generated JSON is written with `newline="\n"`.
  - **Evidence:** `git check-attr` per file; `cmp` shows `starter_kit/` byte-identical to the provided kit; a test asserts no CR bytes in generated JSON.
- **Pins:**
  - **Decision:** exact versions that ran in `.venv`, including numpy 2.5.4 (pulled in by `transformers`) and pandas 3.0.6. At the user's request, pandas was installed into the venv before pinning, so the pin is a tested version.
  - **Note:** global Python has pandas 2.3.3. pandas 3 is a new major version, so check Part B code against it.

## D-13 A2 pre-registered verdicts — Decided by user (2026-10-21, before measurement)
Verdicts are fixed before measuring. Every finding is still measured (evidence rule). If a measurement contradicts its verdict, the number is brought to the user; it is never silently relabelled.

| # | Location | Verdict | Key measurement |
|---|---|---|---|
| F1 | `fertility.py` L62 `split(" ")` | Code bug. *Pre-registered* as "small blast radius"; **revised 2026-10-21 after measurement, user-accepted**: material, up to +2.78% fertility on FLORES Kannada (507/2,009 lines) | Δ on toy and FLORES |
| F2 | L64–67 mean of per-line ratios | Method/decision flaw, fixable (not a code bug) | macro vs micro (ratio of totals) |
| F3 | L60 `.lower()` | Code bug: measured text must equal served text; English and Indic counts are separate measurements | Δ on the English baseline and on the hin/eng ratio, under gpt2 and XLM-R |
| F4 | L49 NFC | **Looks suspicious but fine** (user decision); effect is tokenizer-dependent | Δ under gpt2 and XLM-R, recorded as evidence |
| F5 | L25 `random.seed(1337)`, `import random` | Technical debt: unused | Removed in v1; test proves output identical |
| F6 | L33 `add_special_tokens=False` | Under test: possible false fertility if flipped | Δ with special tokens on |
| F7 | Tokens/word as a cost metric | Conceptual flaw | Fertility ratio vs tokens-per-parallel-sentence ratio |
| F8 | `len(line)`; tok/char "confirms" | Conceptual flaw (code points differ by script; shares the numerator, so not independent), measured as a by-product | — |
| F9 | `gpt2` as the instrument | The cost in question is **our** model's ("Serving Hindi will cost us"; FLM-4B, `model_spec.md`). By the user's rule (GPT-2 cost -> validity flaw; our-model cost -> conceptual flaw), this is a **conceptual flaw** | gpt2 vs Llama-3.2-3B proxy ratios |

Scope: script and metric (F1–F9), plus an audit of REPORT_v0 §1 claims in `partA/A2_audit.md`.

## D-14 A2 effect metric and threshold — Decided (pre-registered 2026-10-21)
- **Metrics:** the numbers the report itself uses. Per-language fertility (tok/word), tok/char, and cross-language ratios vs English. FLORES adds kan and tam.
- **Effect:** Δ% = (variant − v0) / v0 × 100, reported per metric, with direction.
- **Negligible:** |Δ| < 1% on every reported metric **and** the report's conclusion is unchanged. Otherwise "material", reported with magnitude.
- **Order of reporting:** isolated delta per fix (vs v0), then leave-one-out ablation from v1, then cumulative. Each step gets a note.
- This threshold is fixed for A2 and will not be changed after seeing results.
- **Amendment 1 (2026-10-21, user decision):**
  - **What changes:** the "report's conclusion unchanged" half of the rule is **not yet operationalised**. It will be defined after all F1–F9 metrics have been seen, then amended in as they are reviewed.
  - **Disclosure:** this half is therefore *post-hoc*, and the audit must say so wherever it is used.
  - **What doesn't change:** the 1% numeric half is unchanged and still pre-registered. Until then the harness reports the 1% half only, at three levels: corpus overall, per language (incl. ratios vs eng), and per language own metrics.
- **Amendment 2 (2026-10-22, proposed, awaiting user confirmation; post-hoc):**
  - **Rule:** a fix "changes the report's conclusion" if it changes the Hindi multiplier at the report's own precision (≈6×, nearest integer), or breaks the claims "the two metrics agree" or "a property of the script".
  - **Applied:** F7, F8 and F9 change the conclusions; F1–F6 do not. F3 moves FLORES gpt2 hin from 6.10 to 6.32, still ≈6×.
  - **Disclosure:** labelled post-hoc in `partA/A2_audit.md`.

## D-16 V1 denominator = tokens per parallel sentence — Provisional (2026-10-22, autonomous run; for user review)
- **Problem:** F7 shows tokens per word is not a cost ratio. V1 needs *some* denominator.
- **Choice:** `sentence`, because parallel sentences hold content constant (D-06; Petrov et al. §3).
- **Consequence:** in V1, F1 and F2 contribute exactly 0 (ablation). They matter only for the per-word metric.
- **Open:** whether this is *the* single routing/cost number is A3's decision. It needs CIs, ≥2 tokenizers, a per-request overhead model and output tokens.

## D-17 F9 classification and the FLM-4B proxy — Decided (user rule, 2026-10-21)
- **Classification:** REPORT_v0 says "Serving Hindi will cost **us**", meaning our model (FLM-4B). By the user's rule, measuring it with gpt2 is a **conceptual flaw**.
- **Measured with the Llama-3.2-3B proxy (D-04):** hin per-sentence ratio is 7.44 (gpt2) -> 2.53 (proxy), FLORES, V1.
- **Caveat:** a proxy, not FLM-4B's actual tokenizer (parameter count differs).

## D-15 Jev (TypeSafe AI hosted classifier) — Rejected for A1–A4/B; pattern noted for Part C (2026-10-21)
- **What it is:** a hosted, typed classification model (yes/no, choice, ordered score) with claimed calibration. It does not generate text.
- **Properties (secondary sources):**
  - early access only; English-first ("other languages … not equally well");
  - probabilistic;
  - vendor-only benchmarks;
  - one practitioner test titled "noticeably less accurate".
- **Rejected because:**
  - A2/A3 are exact, reproducible counting, and the evidence rule plus the live defense need rerunnable scripts.
  - For A1 and A4, deterministic script detection and the existing metadata already cover the need.
  - Part C forbids external API spend, and four of six target languages have no native reviewer to validate it.
- **Kept:** the *pattern* (a calibrated, ordered-score judge), possibly built from a local open multilingual model and calibrated on reviewer labels. To be evaluated in Part C.
- **Sources:**
  - mindstudio.ai/blog/what-is-jev-classifier-model
  - innfactory.ai/en/blog/jev-system-one-model-classifier-not-llm
  - qapilot hashnode test (title and comments only)
