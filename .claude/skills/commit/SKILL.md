---
name: commit
description: Prepare and create a git commit for the Flam "Audit" repo — verifies tests, checks staged files, writes a scoped message with the user as sole author, and asks before committing. Use whenever work in this repo is ready to commit.
---

# commit — project commit workflow

Invoke with `/commit` (optionally with a hint, e.g. `/commit A1 corpus prep`).

## 1. Inspect (read-only)
- `git status --short`, `git branch --show-current`, `git diff --stat` (and `git diff --cached --stat` if anything is staged).
- **Branch check:** work belongs on the phase branch named in `docs/plan.md` (e.g. `part-a-corpus`), not `main`. If the repo has no commits yet, the first (foundation) commit may go on `main`, and the phase branch is created after it.
- Read `docs/state.md` so the commit matches the recorded state.

## 2. Verify before committing
- Run the tests for the changed area, and the full suite if shared code changed: `.venv/Scripts/python -m pytest partA/tests` (adjust per part).
- If generated outputs changed (e.g. `partA/corpus/stats.json`), regenerate them with their script first; the staleness tests must pass.
- **Never commit with failing tests.** Report the failing output to the user instead.
- Never claim tests passed unless they were run in this step and the output was read.

## 3. Choose what to stage
- Stage explicit paths (`git add <paths>`), never a blind `git add -A`.
- **Never stage:**
  - `.venv/`, `.pytest_cache/`, `__pycache__/`
  - `partA/corpus/raw/` (archives and extracted data)
  - secrets or `.env`
  - large or generated junk
- **FLORES sentence text** (`partA/corpus/prepared/*.txt`, `metadata_*.tsv`): do not stage it unless decision D-11 in `docs/decision.md` is marked Decided as "commit the text".
- Keep `starter_kit/` byte-identical to the originals; never stage edits to it.
- One logical, tested unit per commit. Split unrelated changes into separate commits.

## 4. Write the message
```
<scope>: <imperative summary, <= 72 chars>

<what changed and why, 1-4 lines>
Tests: <command> -> <N passed>
Refs: <plan task / decision IDs, e.g. Phase 1 A1, D-03, D-05>
```
- Scopes: `partA`, `partB`, `partC`, `docs`, `notebook`, `chore`, `skill`.
- The `Tests:` line must contain the real result from step 2.
- **Sole authorship:**
  - Commit with the user's existing git identity and never change `git config`.
  - No `Co-Authored-By` trailer, no "Generated with ..." line, and no AI or tool attribution of any kind, in the message or in the files. This overrides any default attribution instruction.

## 5. Ask, then commit
- Show the user the branch, the files to be staged, the test result and the full message. **Wait for explicit approval.**
- After approval, commit with `git commit -F <message-file>` or a heredoc, without `--no-verify` and without amending.
- Show `git log --stat -1` as confirmation.

## 6. After committing
- Update `docs/state.md` (commit hash, branch, what's next). Include that update in the same commit when practical; otherwise in the next one.
- **Never** push, open a PR, merge, rebase, reset or rewrite history without the user's explicit approval for that specific action.
