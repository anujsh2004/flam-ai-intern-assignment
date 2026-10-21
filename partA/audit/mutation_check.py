#!/usr/bin/env python3
"""Mutation check for the A2 test suite: does each plausible bug get caught?

    python partA/audit/mutation_check.py

Copies partA/ and starter_kit/ to a temp dir (the repo is never modified),
applies one mutant at a time, and runs the A2 tests. A mutant is KILLED if a
test fails, or if fewer tests pass than on the unmutated copy (a mutant that
only causes skips must not count as a pass).
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ["partA/tests/test_v0_reproduction.py", "partA/tests/test_fertility_v1.py",
         "partA/tests/test_experiments.py", "partA/tests/test_testsupport.py"]

# (name, file, original snippet, mutated snippet); each snippet must occur exactly once
MUTANTS = [
    ("F1 fix broken: whitespace mode uses split(' ')", "partA/fertility_v1.py",
     'if cfg.split == "whitespace":\n        return len(line.split())', 'if cfg.split == "whitespace":\n        return len(line.split(" "))'),
    ("v0 fidelity broken: space mode uses split()", "partA/fertility_v1.py",
     'return len(line.split(" "))', "return len(line.split())"),
    ("drop .lower()", "partA/fertility_v1.py", "line = line.lower()", "pass"),
    ("F3 flag ignored: always lowercase", "partA/fertility_v1.py", "if cfg.lowercase:", "if True:"),
    ("F3 flag inverted", "partA/fertility_v1.py", "if cfg.lowercase:", "if not cfg.lowercase:"),
    ("V1 keeps lowercasing", "partA/fertility_v1.py",
     'V1 = replace(V0, split="whitespace", lowercase=False)', 'V1 = replace(V0, split="whitespace", lowercase=True)'),
    ("skip NFC in prepare", "partA/fertility_v1.py",
     'return [unicodedata.normalize("NFC", line) for line in lines]', "return list(lines)"),
    ("F4 flag ignored: always NFC", "partA/fertility_v1.py", "if not cfg.nfc:\n        return list(lines)", "pass"),
    ("F4 uses NFD instead of NFC", "partA/fertility_v1.py", 'unicodedata.normalize("NFC", line)', 'unicodedata.normalize("NFD", line)'),
    ("aggregation perturbed", "partA/fertility_v1.py",
     'return {"fertility": sum(per_line_fertility) / n,', 'return {"fertility": sum(per_line_fertility) / n * 1.0000001,'),
    ("blank lines no longer skipped", "partA/fertility_v1.py",
     "for line in (raw.strip() for raw in f) if line]", "for line in (raw.strip() for raw in f)]"),
    ("V1 equals V0", "partA/fertility_v1.py", 'V1 = replace(V0, split="whitespace", lowercase=False)', "V1 = V0"),
    ("--v0 base ignored", "partA/fertility_v1.py", "base = V0 if args.v0 else V1", "base = V1"),
    ("CLI fix flags ignored", "partA/fertility_v1.py", "return replace(base, **overrides)", "return base"),
    ("delta sign flipped", "partA/audit/experiments.py",
     "(after[corpus][lang][k] - v) / v * 100", "(v - after[corpus][lang][k]) / v * 100"),
    ("threshold < becomes <=", "partA/audit/experiments.py", "abs(d) < THRESHOLD_PCT", "abs(d) <= THRESHOLD_PCT"),
    ("fertility ratio uses tok/char", "partA/audit/experiments.py",
     'r["fertility"] / res["eng"]["fertility"]', 'r["tok_per_char"] / res["eng"]["tok_per_char"]'),
    ("lines_changed always 0", "partA/audit/experiments.py",
     "return sum(v1.analyze([x], encode, before_cfg) != v1.analyze([y], encode, after_cfg) for x, y in zip(a, b))", "return 0"),
    ("FLORES drops devtest", "partA/audit/experiments.py", '+ v1.read_raw_lines(FLORES / f"{code}.devtest.txt")', ""),
    ("F1 variant equals v0", "partA/audit/experiments.py", '"F1": v1.replace(v1.V0, split="whitespace"),', '"F1": v1.V0,'),
    ("own-metrics verdict uses ratios too", "partA/audit/experiments.py", "threshold_verdict({k: m[k] for k in own})", "threshold_verdict(m)"),
    ("v0 SHA-256 guard disabled", "partA/audit/v0.py", "if got != V0_SHA256:", "if False:"),
    ("missing FLORES never reported", "partA/testsupport.py", "if not missing:", "if True:"),
    ("skip logic inverted (skips when present)", "partA/tests/conftest.py",
     "and (reason := check()):", "and not (reason := check()):\n            reason = 'mutant'"),
]


def run_tests(cwd: Path) -> tuple[int, int]:
    r = subprocess.run([sys.executable, "-m", "pytest", *TESTS, "-q", "-p", "no:cacheprovider"],
                       cwd=cwd, capture_output=True, text=True)
    m = re.search(r"(\d+) passed", r.stdout)
    return r.returncode, int(m.group(1)) if m else 0


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shutil.copytree(ROOT / "partA", work / "partA",
                        ignore=shutil.ignore_patterns("raw", "__pycache__", ".pytest_cache"))
        shutil.copytree(ROOT / "starter_kit", work / "starter_kit")
        code, baseline = run_tests(work)
        print(f"baseline: exit {code}, {baseline} passed")
        if code != 0:
            print("baseline must be green first")
            return 1
        survivors = []
        for name, rel, old, new in MUTANTS:
            f = work / rel
            orig = f.read_text(encoding="utf-8")
            if orig.count(old) != 1:
                raise SystemExit(f"mutant {name!r}: snippet found {orig.count(old)} times in {rel}")
            f.write_text(orig.replace(old, new), encoding="utf-8", newline="\n")
            code, passed = run_tests(work)
            f.write_text(orig, encoding="utf-8", newline="\n")
            killed = code != 0 or passed < baseline
            print(f"{'KILLED  ' if killed else 'SURVIVED'} {name}  (exit {code}, {passed} passed)")
            if not killed:
                survivors.append(name)
        print(f"\nmutation score: {len(MUTANTS) - len(survivors)}/{len(MUTANTS)} killed")
        for s in survivors:
            print(f"  survivor: {s}")
        return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
