# A3 — Corrected cross-language analysis

Every number carries an evidence ID `[A#]`. The **Evidence index** at the end maps each ID to its JSON source, and `partA/tests/test_a3_evidence.py` checks every entry. The full generated tables are in [`A3_results.md`](A3_results.md).

## The answer

**The single number that should drive routing and cost is the *tokens-per-parallel-sentence premium versus English*, measured with the *serving model's tokenizer*, as a ratio of totals.**

On FLORES (2,009 parallel sentences), with the Llama-3.2-3B tokenizer as the FLM-4B proxy (95% article-clustered CI):

| | Hindi | Kannada | Tamil |
|---|---|---|---|
| premium vs English | **2.53** [2.50, 2.55] | **8.87** [8.77, 8.96] | **7.63** [7.55, 7.71] |

[A1–A9]

**Meaning:** serving the same content costs about 2.5× English's tokens in Hindi, but about 8–9× in Kannada and Tamil.

**Correction to REPORT_v0:**
- **Report's claims:** Hindi "~6×" [REPORT_v0], and a single "Indic" cost class.
- **Corrected:** Hindi is cheaper than the report says, the Dravidian languages are far costlier, and the cost problem is mainly a **Dravidian** one.

## Why this denominator: what it holds constant

The hint asks what the denominator should hold constant across languages. For a cost decision it must hold **content** constant, because leadership pays tokens to serve *the same request* in different languages.
- **Parallel sentences do this by construction.** Each FLORES line is a professional translation of the same English sentence (A1).
- **Every other unit changes with the language even when the content is identical** (A1): Hindi uses 1.17× English's whitespace words [A20], Kannada 0.74× [A21]. Code points, graphemes and bytes vary with script and orthography. Dividing by them mixes tokenizer efficiency with writing-system properties.

The evidence uses the same tokens (Llama proxy, Hindi) and only changes the denominator. The "premium" swings from 0.99× to 3.86×:

| per word | per code point | per grapheme | per UTF-8 byte | **per parallel sentence** |
|---|---|---|---|---|
| 2.16 [A10] | 2.53 [A11] | 3.86 [A12] | 0.99 [A13] | **2.53** [A1] |

**Notes on the table:**
- **Per byte** says Hindi is *cheaper* than English, which is false for token cost. It reflects that Devanagari takes 3 UTF-8 bytes per code point.
- **Per word** understates Hindi because Hindi splits the same content into more words.
- **Per code point** happens to match the sentence premium for Hindi, because Hindi and English use almost the same number of code points for the same content (A1: 1.00×). That's a coincidence of this language pair, not a property that transfers: it doesn't hold for Kannada or Tamil.

## Why this tokenizer: the instrument decides the number

Same text, same denominator (Hindi per sentence), four tokenizers:

| tokenizer | gpt2 (the report's) | **Llama-3.2-3B (serving proxy)** | XLM-R | IndicBERT v2 |
|---|---|---|---|---|
| hin | 7.44 [A14] | **2.53** [A1] | 1.25 [A15] | 1.17 [A16] |
| kan | 13.59 [A17] | **8.87** [A4] | 1.36 [A18] | 1.10 [A19] |

- **The tokenizer choice moves the Hindi premium about 6×.** A cost number is only meaningful in the tokens of the model that is actually served, so gpt2's 7.44 measures the wrong bill (A2/F9).
- **The pre-registered ranking held for all three languages:** IndicBERT < XLM-R < Llama < gpt2.

## Why a ratio of totals, and how robust it is

- **Billing sums tokens.** A per-line mean over-weights short lines (A2/F2).
- **Robustness:** the median per-sentence premium for Hindi is 2.52 [A23], almost equal to the ratio of totals (2.53). So the headline is not driven by a few long sentences.
- **The spread is wide:** p10 2.00 [A24], p90 3.16 [A25]. Kannada's p90 is 11.32 [A26]. Individual requests vary a lot around the average, which matters for per-request latency and context-window headroom. That goes in A4, not in the cost average.
- **Sampling uncertainty is small.** The CIs are about ±1%, so every difference above is far larger than the noise. The CIs resample whole FLORES articles, because 3–5 sentences are drawn from each one.

## Per-request overhead (input side of the cost model)

Each request pays the tokenizer's special tokens; Llama adds 1 BOS. With the worst-case assumption of one sentence per request, the Hindi premium moves from 2.53 to 2.47 [A27] and Kannada from 8.87 to 8.58 [A28].
- **Effect:** the fixed cost dilutes the premium slightly. That makes the plain sentence premium the conservative choice.
- **Real requests:** they contain more text than one sentence, so the real effect is smaller.

Output tokens are **not** in A3 (scope agreed). A4 states the assumption that replies are in the user's language with a similar premium.

## When another number would be the right one

| Question | Better number |
|---|---|
| Tokenizer efficiency within *one* language, where morphology is fixed | tokens per word (fertility) is fine there |
| Storage, bandwidth, payload size | bytes |
| Display or character-limit UX | graphemes |
| Latency SLOs, context-window headroom per request | per-sentence p90, not the mean |
| Cost if Indic traffic were routed to an Indic-specialised model | the premium under *that* model's tokenizer. IndicBERT shows the vocabulary upside (hin 1.17, kan 1.10) but is an encoder. Sarvam-1 (a generative Indic LM) is the realistic candidate; it was not measured because of its non-commercial licence (D-18). |

## Checked against pre-registration (D-18)

- ✅ **Ranking:** IndicBERT < XLM-R < Llama < gpt2 for hin, kan and tam.
- ❌ **"The sentence premium sits between the per-word and per-byte premiums":** false for Hindi. Under gpt2, sentence 7.44 [A14] > word 6.34 [A22], because Hindi needs 1.17× English's words for the same content [A20]. True for Kannada and Tamil. Recorded as a wrong prediction, not explained away.

## Caveats

- **Proxy tokenizer:** Llama-3.2-3B is a proxy; FLM-4B's config matches on architecture numbers but not on parameter count (D-04).
- **Domain:** FLORES is formal, English-sourced, native-script text. Chat, code-mixed and romanised traffic (e.g. Hinglish) are untested and could shift the premiums either way.
- **Scope:** input tokens only. One sentence per request is the overhead's worst case, not a traffic model.

## Evidence index

ID | file | JSON path | value as quoted (CIs are listed as their point, lo and hi entries).

| ID | file | path | value |
|---|---|---|---|
| A1 | partA/analysis/results.json | by_tokenizer.llama.premium.hin.sentence.0 | 2.53 |
| A2 | partA/analysis/results.json | by_tokenizer.llama.premium.hin.sentence.1 | 2.50 |
| A3 | partA/analysis/results.json | by_tokenizer.llama.premium.hin.sentence.2 | 2.55 |
| A4 | partA/analysis/results.json | by_tokenizer.llama.premium.kan.sentence.0 | 8.87 |
| A5 | partA/analysis/results.json | by_tokenizer.llama.premium.kan.sentence.1 | 8.77 |
| A6 | partA/analysis/results.json | by_tokenizer.llama.premium.kan.sentence.2 | 8.96 |
| A7 | partA/analysis/results.json | by_tokenizer.llama.premium.tam.sentence.0 | 7.63 |
| A8 | partA/analysis/results.json | by_tokenizer.llama.premium.tam.sentence.1 | 7.55 |
| A9 | partA/analysis/results.json | by_tokenizer.llama.premium.tam.sentence.2 | 7.71 |
| A10 | partA/analysis/results.json | by_tokenizer.llama.premium.hin.words.0 | 2.16 |
| A11 | partA/analysis/results.json | by_tokenizer.llama.premium.hin.codepoints.0 | 2.53 |
| A12 | partA/analysis/results.json | by_tokenizer.llama.premium.hin.graphemes.0 | 3.86 |
| A13 | partA/analysis/results.json | by_tokenizer.llama.premium.hin.bytes.0 | 0.99 |
| A14 | partA/analysis/results.json | by_tokenizer.gpt2.premium.hin.sentence.0 | 7.44 |
| A15 | partA/analysis/results.json | by_tokenizer.xlmr.premium.hin.sentence.0 | 1.25 |
| A16 | partA/analysis/results.json | by_tokenizer.indicbert.premium.hin.sentence.0 | 1.17 |
| A17 | partA/analysis/results.json | by_tokenizer.gpt2.premium.kan.sentence.0 | 13.59 |
| A18 | partA/analysis/results.json | by_tokenizer.xlmr.premium.kan.sentence.0 | 1.36 |
| A19 | partA/analysis/results.json | by_tokenizer.indicbert.premium.kan.sentence.0 | 1.10 |
| A20 | partA/corpus/stats.json | ratio_vs_eng.hin_Deva.words.0 | 1.17 |
| A21 | partA/corpus/stats.json | ratio_vs_eng.kan_Knda.words.0 | 0.74 |
| A22 | partA/analysis/results.json | by_tokenizer.gpt2.premium.hin.words.0 | 6.34 |
| A23 | partA/analysis/results.json | by_tokenizer.llama.spread.hin.median | 2.52 |
| A24 | partA/analysis/results.json | by_tokenizer.llama.spread.hin.p10 | 2.00 |
| A25 | partA/analysis/results.json | by_tokenizer.llama.spread.hin.p90 | 3.16 |
| A26 | partA/analysis/results.json | by_tokenizer.llama.spread.kan.p90 | 11.32 |
| A27 | partA/analysis/results.json | by_tokenizer.llama.premium_with_overhead.hin.0 | 2.47 |
| A28 | partA/analysis/results.json | by_tokenizer.llama.premium_with_overhead.kan.0 | 8.58 |
