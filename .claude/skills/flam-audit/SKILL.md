---
name: flam-audit
description: Project workflow for the Flam AI intern "The Audit" assignment (tokenizer audit, serving capacity reconciliation, decision memo). Use when starting, continuing, testing, documenting, or committing any work in this repo.
---

# flam-audit — project workflow

Invoke with `/flam-audit` (optionally with the task, e.g. `/flam-audit start B1`), or let it load automatically for work in this repo.

## Before any task
1. Read `docs/state.md` (where we are), then `docs/plan.md` (what's next, dependencies), then relevant entries in `docs/decision.md`.
2. Re-read the assignment text for the task: `C:\Users\anuj1609\OneDrive\Desktop\Flam_assignment documents\AI ASSIGNMENT 2026.pdf` (extract with `pdftotext -layout`). The Word summary is a reference only; the PDF wins on conflict.
3. Inspect `git status` and the current branch. Work on the phase branch named in `plan.md`; never on `main` directly.

## Rules
- **Evidence rule:** every claimed flaw/metric/config effect needs the exact command, before/after numbers, and one sentence on why the delta proves it. Unverified claims are penalised (-5 each); fabricated evidence fails the assignment. Test a suspicion before calling it a bug; record harmless findings too.
- **Never claim a test, experiment, or validation passed unless it was run and the output was read.** Report failures with output. Hypotheses are labelled as hypotheses.
- **TDD:** write the test -> run it, confirm it fails for the intended reason -> minimal implementation -> run, confirm it passes -> refactor -> run regressions (`pytest`).
- **BDD:** express requirements as Given/When/Then (in test names/docstrings or `docs`), traceable to a plan task and a commit.
- **Alternatives:** for any significant choice (corpus, tokenizer, library, approach) list alternatives, criteria, run a fair experiment (same data, splits, preprocessing), then record in `decision.md`. Cite only sources actually read; X/Twitter posts are supplementary context, not proof.
- **Understandable by the author:** the user must defend everything live. Prefer simple code; explain non-obvious steps; no code or number the user cannot re-derive.
- **Small steps:** one task at a time; explain the requirement and approach, ask when a choice materially changes direction, then implement.

## After a task
1. Run relevant tests and regression (`python -m pytest`).
2. Append a chronological entry to `NOTEBOOK.md` (hypothesis -> experiment -> result -> revision, including dead ends).
3. Update `docs/plan.md` checkboxes, `docs/state.md`, and `docs/decision.md` (keep the three consistent with the repo).
4. Commit small, tested units via the `/commit` skill (`.claude/skills/commit/SKILL.md`).

## Git and authorship
- The user is the **sole author**. Never add `Co-Authored-By`, "Generated with ..." or any tool/AI attribution to commits, PRs, or files.
- Do not push, open PRs, merge, delete work, or rewrite history without explicit user approval.
- Do not commit secrets, large raw datasets, caches or generated junk (respect `.gitignore`).
- Never edit `starter_kit/` (originals); copy into `partA/` to modify.
