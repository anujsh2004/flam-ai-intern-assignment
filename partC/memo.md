# Decision memo — casual replies in Hindi, Kannada, Tamil, Telugu, Bengali, Marathi

**Recommendation:**
- **(c) Prompt engineering is the launch path.**
- **(a) LoRA SFT on synthetic casualised pairs is the fallback.**
- **Reject (b), the 1B rewriter.**

Launch in **Hindi and Kannada**, the two languages our reviewer can validate. Run Telugu, Tamil, Bengali and Marathi behind automated checks (back-translation meaning check, formality proxies) and enable them after native validation.

**Why:** the binding constraint is **20 reviewer-hours in 2 languages**, not GPU.
- **Prompting** costs no GPU and can be tested on day 1.
- **SFT** is cheap to train, but its synthetic data can only be spot-checked.
- **A rewriter** has SFT's data problem *plus* a permanent serving cost.

## Assumptions
- **Model:** the assistant is FLM-4B-Instruct on Part B's 1× L4 stack.
- **Reviewer:** 60 judgements/h, each one prompt + reply on 2 yes/no questions. Checked at 30/60/90; **measured on day 1**.
- **Token premiums vs English (A3, serving tokenizer):** hin **2.53**, kan **8.87**.
- **Synthetic data:** 2,000 pairs per launch language, about 200 English-equivalent tokens each, 3 epochs.
- **A100:** 312 TFLOPS bf16 at 40% MFU; 6 FLOPs per parameter per token.
- **Thresholds:** judgement-based starting points, to agree with product.

## Back-of-envelope arithmetic (`python partC/arithmetic.py`)
- **Reviewer:** 10 h/week × 2 GPU weeks = **20 h**, which is **600 / 1,200 / 1,800** judgements at 30/60/90 per hour.
  - **Week 1:** 50 calibration + 2 variants × 2 languages × 100 screening, with 150 spare.
  - **Week 2:** 2 × 200 final evaluation + 200 synthetic spot checks.
  - At 30/h it does not fit: use 1 variant and n=100.
- **SFT fallback:** **506** (hin) and **1,774** (kan) tokens per pair; **13.7M** tokens in total, about **0.8 GPU-hours** of LoRA.
  - Full fine-tuning needs **67.2 GB** of optimiser state before activations, so LoRA (base weights **8.4 GB**).
  - The risk is data quality, not GPU time: about 200 of 4,000 pairs can be reviewed.
- **Rewriter:** a 1B model re-generating every reply adds about **24%** decode work per request. That means about **19%** fewer requests per L4, which Part B shows is already capacity-bound. It also adds latency, and still needs casual training data.

## Success metric
On 200 held-out prompts per launch language, blind pairwise against current replies:
- **≥ 70% casual-enough** (± 6.4 pts at n=200; the lower bound is still a clear majority);
- **and ≥ 95% meaning and help preserved** (± 3.0 pts). Tone must not cost correctness.

## Kill criterion
- **Day 5:** best prompt **< 50% casual** on hi/kn -> **switch to LoRA SFT**, using the best prompt as the pair generator. That leaves 9 GPU days.
- **Day 12:** SFT **< 70% casual or < 95% meaning** -> launch hi/kn with the best variant that keeps ≥ 95% meaning, or **defer**.

## Day-1 experiment
1. Write 2 prompt variants for hi/kn: an explicit casual-register instruction, and the same plus 3 reviewer-approved examples.
2. Generate replies to 100 fixed prompts per language, with each variant and with the current prompt.
3. The reviewer rates **50 blind pairs**.

This yields three things: the reviewer's **real judgements/hour**; whether prompting moves casualness at all; and whether our cheap formality checks agree with the reviewer well enough to monitor te/ta/bn/mr.
