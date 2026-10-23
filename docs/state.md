# Project state

_Last updated: 2026-10-23. **All parts complete** and merged into `main` locally. Remaining: `AI_USAGE.md` (author), push to GitHub (after user approval), optional defense cheat sheet._

## Status by part
| Part | Deliverable | Headline | Merged into `main` |
|---|---|---|---|
| A1 | `partA/corpus/README.md` | FLORES-200 dev+devtest, eng/hin/kan/tam, 2,009 parallel sentences; limits documented | `48f28fe` |
| A2 | `partA/A2_audit.md`, `A2_results.md` | 9 findings. F1/F2/F3 material; F4/F6 fine as written; F5 debt; F7/F8/F9 conceptual, with F9 (wrong instrument) largest. Report's 5.887 reproduced exactly. | `c155ad7` |
| A3 | `partA/A3_analysis.md`, `A3_results.md` | Cost number: tokens per parallel sentence vs English, serving tokenizer (Llama-3.2-3B proxy). hin **2.53×**, kan **8.87×**, tam **7.63×** (95% CI ±~1%). | `09a3d15` |
| A4 | `partA/A4_memo.md` | Budget per language; pressure is Dravidian (98.1% / 89.2% byte-fragment tokens); biggest caveat the proxy tokenizer; monitor tokens per code point by language and script, ±20% weekly | `f68e25a` |
| B | `partB/answers.md` | 114,688 B/token; ~25 concurrent 4K sequences (decimal GB, log-confirmed); goodput peaks at b24 then preemption; cap at 24 (+23.8%), fp8 KV as follow-up; `reported_tok_s` counts prompt + gen; b24 goodput 200.9 tok/s; counter `vllm:num_preemptions_total` | `fc2a4a5` |
| C | `partC/memo.md` | Prompt-only launch for hi+kn; LoRA SFT fallback; rewriter rejected (+24% decode work); ≥70% casual / ≥95% meaning; kill at day 5 / day 12 | `dfeace8` |

## Final verification (2026-10-23; all run, outputs read)
- **Full suite:** `python -m pytest partA/tests partB/tests partC/tests` -> **363 passed**, on `main` after the A4 merge.
- **Fresh `git clone` of `main`** (`f68e25a`, 155-character path):
  - without FLORES text: 302 passed, 61 skipped, 0 failed;
  - `prep.py` from scratch: hash-checked, `manifest.json` identical to the committed one;
  - then the full suite: **363 passed**;
  - clone working tree unchanged afterwards (no generated-file drift).
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
1. `AI_USAGE.md`: written by the user (required by the assignment).
2. Push to GitHub: only after the user approves.
3. Defense cheat sheet: offer to the user (reminder owed).

## Environment
- **Venv:** `.venv` on Python 3.14.0 with pinned `requirements.txt`.
- **Tokenizers:** pinned revisions; the Llama tokenizer is gated (licence + `hf auth login`).
- **Git:** `core.autocrlf=true`, overridden by `.gitattributes`.
- **Decisions:** D-01 … D-20 in `docs/decision.md`.
