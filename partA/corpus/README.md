# A1 — Evaluation corpus

**Corpus:** FLORES-200, `dev` + `devtest`, four languages: English (`eng_Latn`), Hindi (`hin_Deva`), Kannada (`kan_Knda`), Tamil (`tam_Taml`). Kannada and Tamil are the two Dravidian languages.
Why this corpus and not the alternatives: see [decision D-03](../../docs/decision.md#d-03-evaluation-corpus-source-a1).

## Reproduce

```
python -m venv .venv && .venv/Scripts/python -m pip install pytest regex
.venv/Scripts/python partA/corpus/prep.py     # downloads (if absent), verifies SHA-256, writes prepared/ + manifest.json
.venv/Scripts/python partA/corpus/stats.py    # writes stats.json (all numbers below)
.venv/Scripts/python -m pytest partA/tests    # alignment, integrity and stats-consistency checks
```

Archive: `https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz`, 25,585,843 bytes, SHA-256 `b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6` (checked by `prep.py`).

## Size and source

| | dev | devtest | total |
|---|---|---|---|
| parallel sentences (per language) | 997 | 1,012 | **2,009** |
| source articles (unique URLs) | 281 | 281 | 562 |
| wikinews / wikibooks / wikivoyage | 348 / 301 / 348 | 341 / 351 / 320 | 689 / 652 / 668 |

Article counts match the FLORES-101 paper (Table 1: dev 281, devtest 281 articles). "wikibooks" in the metadata corresponds to what the paper calls Wikijunior (children's non-fiction books).

**Domain:** written, edited, encyclopedic/news/travel-guide prose. Top topics (case-folded): travel 497, sports 101, politics 90, crime and law 80, health 44, safety 40, science 39. About a quarter of the sentences are about travel.

**How it was made (per Goyal et al., FLORES-101):** English sentences were selected from random articles, typically 3–5 contiguous sentences per article. Professional translators then translated them *from English*, with automatic checks and human quality scoring against a 90/100 threshold. So every non-English line is a human translation of the English line on the same row.

## Preprocessing

**None applied to the text.** The prepared files are byte-for-byte copies of the archive members. Each decision was checked, not assumed:

| Step | Decision | Evidence |
|---|---|---|
| Line alignment | Kept as distributed | Equal counts (997 and 1,012) in all languages. English lines with a 2+ digit number have it in the translation 99.7% (hi), 99.7% (kn), 99.2% (ta) of the time (368 lines checked). Char-length ratio vs English: 0.49–2.03, 0 lines outside 0.2–5. |
| Deduplication | Not needed | 0 duplicate lines in any language |
| Empty lines / encoding | None found | Strict UTF-8 decode passes. No blank lines, no `\r`. |
| Lowercasing | Not applied | Would change English token counts. It is an A2 audit question, not a corpus step. |
| Unicode NFC | **Measured, not applied** | Lines changed by NFC (dev/devtest): eng 0/0, hin 90/93 (~9%), kan 10/7, tam 2/2. In Hindi this is the precomposed nukta letters (U+095B ज़, U+095C ड़, U+095E फ़, U+095D ढ़, …), which NFC *decomposes*. Keeping the raw text lets A2 measure NFC's effect on token counts. |

## Text-unit totals (all 2,009 sentences)

Ratios are *ratio of totals* vs the parallel English text. The 95% CIs come from a bootstrap that resamples whole articles.

| | words (whitespace) | code points | grapheme clusters | UTF-8 bytes |
|---|---|---|---|---|
| eng | 42,855 | 257,160 | 257,160 | 257,386 |
| hin | 50,250 (**1.17×**, 1.16–1.18) | 256,462 (1.00×, 0.99–1.00) | 168,399 (0.65×) | 659,364 (**2.56×**) |
| kan | 31,530 (**0.74×**, 0.73–0.74) | 270,103 (1.05×, 1.04–1.06) | 176,845 (0.69×) | 733,136 (**2.85×**) |
| tam | 32,909 (**0.77×**, 0.76–0.77) | 300,261 (1.17×, 1.16–1.18) | 194,191 (0.76×) | 820,442 (**3.19×**) |

What this means for A2 and A3. These are observations about the denominators; no tokenizer is involved yet.
- **Words are not a constant unit of content.** The same 2,009 sentences take 17% *more* whitespace words in Hindi but 23–26% *fewer* in Kannada and Tamil, which are agglutinative and fuse words. A tokens-per-word metric therefore inflates Kannada and Tamil and deflates Hindi, before any tokenizer effect.
- **Bytes penalise Indic scripts by construction.** Indic code points are 3 bytes in UTF-8, ASCII is 1, so the same content takes 2.6–3.2× the bytes.
- **Grapheme clusters are not uniform across scripts.** With the `regex` module, a ka+virama+ssa conjunct is 1 cluster in Devanagari but 2 in Kannada and Tamil (pinned in `tests/test_units.py`; see D-05).
- **Sentence parallelism is the unit that holds content constant by design.** That is why A3 will lead with tokens per parallel sentence (the "premium" of Petrov et al., 2023, §3). The other denominators are reported to show the distortion.

**Sample-size check.** The codepoint ratio CI half-width is about 0.7%, and article-clustered vs i.i.d. bootstrap intervals are almost identical (hin: 0.991–1.004 vs 0.991–1.003). Dev and devtest agree within 0.8% (hin 1.0015 vs 0.9933; kan 1.0541 vs 1.0468; tam 1.1672 vs 1.1680). Corpus-level ratios are therefore stable at this size. Token-ratio CIs will be measured separately in A3.

## What this corpus cannot tell us

FLORES measures **edited, formal, written text translated from English**: news, travel guides and children's encyclopedia prose. Production traffic for an Indian assistant is likely very different, and none of these differences is measured here:
- **Register.** Casual chat, which is exactly what Part C cares about, is absent.
- **Translationese.** Every Indic line is translated from English, so sentence structure and named entities follow the English source.
- **Code-mixing and script.** Only 86 Hindi, 133 Kannada and 165 Tamil lines contain any Latin letter (≤0.27% of code points). Romanized Hindi ("Hinglish") and mid-sentence English, both common in real Indian traffic, are missing.
- **Length.** Mean sentence length is 21.3 English words (128 code points), against 7.8 words (45 code points) in the starter toy corpus. Effects that depend on message length, such as fixed per-message overhead or short queries, are under-represented.
- **Coverage.** The corpus covers four languages only. Telugu, Malayalam, Bengali and Marathi, which matter for Part C's language list, are not measured.
- **Possible tokenizer exposure.** Wikipedia-style text may be over-represented in tokenizer training data, which could flatter tokenizers on this domain. This is a hypothesis, not tested.

With 2,009 sentences from 562 articles, corpus-level ratios are stable (±~1%). Per-topic slices (e.g. ~100 sports sentences) and tail statistics (p99 lengths) are not. The corpus can rank tokenizers and denominators on formal written text. It cannot predict the absolute cost multiplier on live traffic; A4 must name the production metric that checks this.

## Licence and attribution

FLORES-200 is licensed **CC BY-SA 4.0** (stated on the Hugging Face dataset card `facebook/flores`). Cite: NLLB Team et al. (2022), *No Language Left Behind*, arXiv:2207.04672; Goyal et al. (2022), *The FLORES-101 Evaluation Benchmark*, TACL 10:522–538; Guzmán et al. (2019), arXiv:1902.01382.
The successor dataset (FLORES+) asks that the data not be used for training and not be redistributed publicly without anti-scraping protection, to protect it as an evaluation set. In that spirit, the **sentence text is not committed** to this repo: `prep.py` regenerates it, with a hash check. Only aggregate statistics are committed.
