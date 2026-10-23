# Decision memo — casual replies in Hindi, Kannada, Tamil, Telugu, Bengali, Marathi

**Recommendation:** **(c) prompt engineering is the launch path**, with **(a) LoRA SFT on synthetic casualised pairs as the planned fallback**. **Reject (b), the 1B rewriter.** Launch the casual style in **Hindi and Kannada**, the two languages our reviewer can validate. Run Telugu, Tamil, Bengali and Marathi behind automated checks as monitoring only, and switch them on after native validation.

**Why:** the binding constraint is **20 reviewer-hours in 2 languages**, not GPU. Prompting spends no GPU and can be tested on day 1. SFT is cheap on the A100 but its synthetic data can only be spot-checked. A rewriter has SFT's data problem *plus* a permanent serving cost.

## Assumptions
- **The assistant is FLM-4B-Instruct on Part B's 1× L4 stack.** The brief names no other model.
- **Reviewer speed:** 60 judgements/h at planning, each judgement being one prompt and reply rated on 2 yes/no questions. The plan is checked at 30/60/90 and **measured on day 1**.
- **Token premiums vs English (A3, serving tokenizer):** hin **2.53**, kan **8.87**. Training data for the same content is that much longer.
- **Synthetic data:** about 200 English-equivalent tokens per pair, 2,000 pairs per launch language, 3 epochs.
- **A100 compute:** 312 TFLOPS bf16 at 40% MFU, and 6 FLOPs per parameter per training token.
- **Thresholds:** the success thresholds are judgement-based starting points, to be agreed with the product team.

## Back-of-envelope arithmetic (`python partC/arithmetic.py`)
- **Reviewer capacity:** 10 h/week × 2 GPU weeks = **20 h**, which is **600 / 1,200 / 1,800** judgements at 30/60/90 per hour. The plan at 60/h:
  - **Week 1:** 50 calibration + 2 prompt variants × 2 languages × 100 = 400 screening, with 150 spare.
  - **Week 2:** 2 × 200 final evaluation + 200 synthetic-pair spot checks.

  At 30/h it does not fit: drop to 1 variant and n=100 for the final evaluation.
- **SFT (fallback):** per pair, **506** tokens (hin) and **1,774** (kan); **13.7M** tokens over 3 epochs, about **0.8 GPU-hours** of LoRA.
  - Full fine-tuning needs **67.2 GB** of optimiser state before activations, too tight on 80 GB, hence LoRA (8.4 GB base weights).
  - GPU time is not the risk. Data quality is: the reviewer can check about 200 of 4,000 pairs.
- **Rewriter (rejected):** decode is memory-bound, so a 1B model that re-generates every reply adds about **24%** decode work per request.
  - That means about **19%** fewer requests per L4, on a stack Part B shows is already capacity-bound (about 25 concurrent 4K sequences).
  - It also adds sequential latency, and still needs casual training data.

## Success metric
On 200 held-out prompts per launch language, blind pairwise against the current replies:
- **≥ 70% judged casual-enough** (95% CI ± 6.4 pts at n=200, so the lower bound is still a clear majority);
- **and ≥ 95% keep the meaning and help** (± 3.0 pts). A tone gain must not cost correctness.

## Kill criterion
- **Day 5:** if the best prompt variant is **< 50% casual** on hi/kn, stop iterating prompts and **switch to LoRA SFT**. The best prompt becomes the synthetic-pair generator. That leaves 9 GPU days.
- **Day 12:** if SFT is still **< 70% casual or < 95% meaning**, launch hi/kn with the best variant that keeps ≥ 95% meaning, or **defer**. That leaves 2 GPU days and week 3 for launch preparation.

## Day-1 experiment
1. Write **2 prompt variants** for hi/kn: (i) an explicit casual-register instruction; (ii) the same plus 3 reviewer-approved casual examples.
2. Generate replies to **100 fixed prompts per language** with each variant and with the current prompt.
3. The reviewer rates **50 blind pairs** on 2 questions (casual? meaning kept?).

This yields (1) the reviewer's **real judgements/hour**, which replaces the 60/h assumption; (2) whether casual style moves *at all* under prompting; (3) agreement between our cheap formality checks and the reviewer, to decide whether those checks are good enough to monitor te/ta/bn/mr.
