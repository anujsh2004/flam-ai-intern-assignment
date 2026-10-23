# Project state

_Last updated: 2026-10-23. **All parts and deliverables complete**, merged into `main`, and verified before push. Remaining: push the final commits to GitHub (after user approval); optional defense cheat sheet._

## Status by part
| Part | Deliverable | Headline | Merged into `main` |
|---|---|---|---|
| A1 | `partA/corpus/README.md` | FLORES-200 dev+devtest, eng/hin/kan/tam, 2,009 parallel sentences; limits documented | `48f28fe` |
| A2 | `partA/A2_audit.md`, `A2_results.md` | 9 findings. F1/F2/F3 material; F4/F6 fine as written; F5 debt; F7/F8/F9 conceptual, with F9 (wrong instrument) largest. Report's 5.887 reproduced exactly. | `c155ad7` |
| A3 | `partA/A3_analysis.md`, `A3_results.md` | Cost number: tokens per parallel sentence vs English, serving tokenizer (Llama-3.2-3B proxy). hin **2.53×**, kan **8.87×**, tam **7.63×** (95% CI ±~1%). | `09a3d15` |
| A4 | `partA/A4_memo.md` | Budget per language; pressure is Dravidian (98.1% / 89.2% byte-fragment tokens); biggest caveat the proxy tokenizer; monitor tokens per code point by language and script, ±20% weekly | `f68e25a` |
| B | `partB/answers.md` | 114,688 B/token; ~25 concurrent 4K sequences (decimal GB, log-confirmed); goodput peaks at b24 then preemption; cap at 24 (+23.8%), fp8 KV as follow-up; `reported_tok_s` counts prompt + gen; b24 goodput 200.9 tok/s; counter `vllm:num_preemptions_total` | `fc2a4a5` |
| C | `partC/memo.md` | Prompt-only launch for hi+kn; LoRA SFT fallback; rewriter rejected (+24% decode work); ≥70% casual / ≥95% meaning; kill at day 5 / day 12 | `dfeace8` |

## Submission check against the brief (2026-10-23)
- **Evidence rule:** completed for all 9 A2 findings (command, before → after, why-sentence), now enforced by a test.
- **Layout:** the README states the repo root is the brief's `your-submission/` folder.
- **`AI_USAGE.md`:** written. It covers where AI was used and to what extent, the user's decisions, testing after every task, and Claude's mistakes.
- **Part C memo:** tightened to 547 words (≤ 550 enforced by a test). The A4 memo is 543 words.
- **Plan:** every to-do item in `docs/plan.md` is ticked.

## Final verification before push (2026-10-23; all run, outputs read)
- **Full suite:** `python -m pytest partA/tests partB/tests partC/tests` -> **381 passed** on `main` (`2284a51`).
- **Fresh `git clone` of that `main`** (156-character path):
  - without FLORES text: 320 passed, 61 skipped, 0 failed;
  - `prep.py` from scratch: hash-checked, `manifest.json` identical to the committed one;
  - then the full suite: **381 passed**;
  - clone working tree unchanged afterwards (no generated-file drift).
- **Assignment checklist:** NOTEBOOK, AI_USAGE, A1–A4, B1–B4 and C all present, with their required sections and length limits.
- **Safety:** no FLORES text, raw archive, venv, `.env` or token-like strings tracked in any commit.
- **Starter kit:** 6/6 files byte-identical to the provided originals (`cmp`); touched only by the initial commit `bd21ead`.
- **Mutation testing:**
  - A2: full run 50/50;
  - A3: targeted 12/12;
  - Part B: targeted 10/10;
  - the final full run was waived by the user (D-19).
- **Authorship:** every commit is by `anujsh2004` only; 0 attribution lines.

## Known limits (stated in the deliverables)
- **Proxy tokenizer:** FLM-4B's real tokenizer is unavailable; it is the biggest caveat.
- **Domain:** FLORES is formal, native-script text; chat, code-mixed and romanised traffic is unmeasured.
- **Log quality:** in the Part B log, the latency columns use a different clock from `wall_clock_s`.
- **Part C:** thresholds and reviewer speed are labelled assumptions; the day-1 experiment measures the latter.
- **Windows clone depth:** cloning into a very deep folder hits MAX_PATH on git's own `.git/hooks` files (any repo). Noted in the README.

## Remaining
1. Push the final commits to GitHub, only after the user approves. The first push of all branches was done earlier at the user's request.
2. Defense cheat sheet: offer to the user (reminder owed).

## Environment
- **Venv:** `.venv` on Python 3.14.0 with pinned `requirements.txt`.
- **Tokenizers:** pinned revisions; the Llama tokenizer is gated (licence + `hf auth login`).
- **Git:** `core.autocrlf=true`, overridden by `.gitattributes`.
- **Decisions:** D-01 … D-20 in `docs/decision.md`.
