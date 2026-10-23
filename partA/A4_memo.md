# A4 — Recommendation memo: tokenizer cost and Indic routing

**To:** leadership · **Re:** REPORT_v0 §1 ("Hindi costs ~6×; route all Indic traffic separately") · **Evidence:** `A2_audit.md`, `A3_analysis.md`

## Corrected headline numbers
REPORT_v0's 5.89× is a faithful output of its script, but it measures the wrong thing with the wrong instrument:
- it divides by words, which do not hold content constant across languages;
- it uses GPT-2, not our serving tokenizer (A2: F7, F9).

**Measured instead:** the **same 2,009 parallel FLORES sentences**, counted with the **serving tokenizer** (Llama-3.2-3B, our proxy for FLM-4B), as **tokens per sentence vs English** (95% CI):

| | Hindi | Kannada | Tamil |
|---|---|---|---|
| **Cost vs English** | **2.53×** [2.50, 2.55] | **8.87×** [8.77, 8.96] | **7.63×** [7.55, 7.71] |

- **The report's own metric with this tokenizer** gives Hindi 2.11×, not 5.89×.
- **Output tokens:** replies are assumed to be in the user's language, so the same multiplier applies to them.

**Why Kannada and Tamil cost more.** It is vocabulary coverage, not the script:
- Same content, similar length: Kannada has 1.05× English's characters, Tamil 1.17×.
- But **98.1%** of Kannada tokens and **89.2%** of Tamil tokens are byte fragments (the tokenizer has no pieces for them), against 0.2% for Hindi.
- An Indic-aware vocabulary (IndicBERT v2) encodes the same Kannada at 1.10×.

## Routing recommendation
1. **Retire the "6× for Hindi" budget.** Budget per language: Hindi ≈2.5×, Kannada ≈8.9×, Tamil ≈7.6× English tokens.
2. **Do not route "Indic" as one class.** Hindi is a moderate premium on the current stack. The cost, latency and context-window pressure is **Dravidian**.
3. **For Kannada and Tamil, evaluate an Indic-capable model or vocabulary before routing anything away.** The token upside is large (≈8.9× down towards ≈1.1×), but a model switch carries quality and operations risk. Sarvam-1 is a candidate we have not tested; its licence is non-commercial.
4. **First action:** re-run `python partA/analysis/premium.py` with FLM-4B's real tokenizer. The decision above rests on it (next section).

## Biggest caveat
**The tokenizer is a proxy.** Every number above uses Llama-3.2-3B's tokenizer.
- **Evidence that FLM-4B is a different model:** it matches the spec on every architecture number but **not** on parameter count (4.2B vs ≈3.2B).
- **Measured sensitivity:** the tokenizer alone moves the answer from **1.17× to 7.44×** for Hindi and **1.10× to 13.59×** for Kannada.
- **Implication:** if FLM-4B's vocabulary covers Kannada and Tamil better, recommendation 2 could shrink or vanish.

**Second, and unmeasured:** FLORES is formal, native-script text. Chat, code-mixed and romanised Hindi ("Hinglish") would tokenise more like English and lower the Hindi premium.

## The one metric to monitor in production
**Tokens per code point, by detected language and script, on live traffic, compared with the FLORES baseline.**
- **Baselines (serving tokenizer):** English 0.21, Hindi 0.52, Kannada 1.74, Tamil 1.35.
- **Alert:** if any language-script cell drifts **±20%** over a week.
- **Why this metric:** live traffic has no parallel English to compare against, so the premium itself cannot be measured in production. Tokens per code point *within* one language and script does not depend on message length.
- **What it catches:**
  - the **biggest caveat** immediately: a better Kannada vocabulary drops it well below 1.74;
  - the **second caveat**: romanised Hindi shows up at English-like values.
