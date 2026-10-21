#!/usr/bin/env python3
"""Mutation check for the A2 test suite: does each plausible bug get caught?

    python partA/audit/mutation_check.py

Copies partA/ and starter_kit/ to a temp dir (the repo is never modified),
applies one mutant at a time, and runs the A2 tests. A mutant is KILLED if a
test fails, or if fewer tests pass than on the unmutated copy (a mutant that
only causes skips must not count as a pass).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ["partA/tests/test_v0_reproduction.py", "partA/tests/test_fertility_v1.py",
         "partA/tests/test_experiments.py", "partA/tests/test_testsupport.py", "partA/tests/test_f5_seed.py",
         "partA/tests/test_ablation.py", "partA/tests/test_report.py", "partA/tests/test_audit_evidence.py"]

# (name, file, original snippet, mutated snippet); each snippet must occur exactly once
MUTANTS = [
    ("F1 fix broken: whitespace mode uses split(' ')", "partA/fertility_v1.py",
     'if cfg.split == "whitespace":\n        return len(line.split())', 'if cfg.split == "whitespace":\n        return len(line.split(" "))'),
    ("v0 fidelity broken: space mode uses split()", "partA/fertility_v1.py",
     'return len(line.split(" "))', "return len(line.split())"),
    ("drop .lower()", "partA/fertility_v1.py",
     "return line.lower() if cfg.lowercase else line", "return line"),
    ("F3 flag inverted", "partA/fertility_v1.py",
     "return line.lower() if cfg.lowercase else line", "return line.lower() if not cfg.lowercase else line"),
    ("V1 keeps lowercasing", "partA/fertility_v1.py",
     'V1 = replace(V0, split="whitespace", lowercase=False,', 'V1 = replace(V0, split="whitespace", lowercase=True,'),
    ("skip NFC in prepare", "partA/fertility_v1.py",
     'return [unicodedata.normalize("NFC", line) for line in lines]', "return list(lines)"),
    ("F4 flag ignored: always NFC", "partA/fertility_v1.py", "if not cfg.nfc:\n        return list(lines)", "pass"),
    ("F4 uses NFD instead of NFC", "partA/fertility_v1.py", 'unicodedata.normalize("NFC", line)', 'unicodedata.normalize("NFD", line)'),
    ("aggregation perturbed", "partA/fertility_v1.py",
     'return {"fertility": sum(per_line_fertility) / n,', 'return {"fertility": sum(per_line_fertility) / n * 1.0000001,'),
    ("F2 totals mode returns per-line mean", "partA/fertility_v1.py",
     'return {"fertility": total_tokens / total_words, "tok_per_char": total_tokens / total_chars}',
     'return {"fertility": sum(per_line_fertility) / len(per_line_fertility), "tok_per_char": total_tokens / total_chars}'),
    ("F2 total tok/char divides by words", "partA/fertility_v1.py",
     '"tok_per_char": total_tokens / total_chars}', '"tok_per_char": total_tokens / total_words}'),
    ("F2 branch inverted", "partA/fertility_v1.py", 'if cfg.aggregate == "line_mean":', 'if cfg.aggregate != "line_mean":'),
    ("V1 keeps line mean", "partA/fertility_v1.py",
     'lowercase=False, aggregate="total", denominator=', 'lowercase=False, aggregate="line_mean", denominator='),
    ("F6 flag ignored: specials always counted", "partA/fertility_v1.py",
     'specials = getattr(encode, "num_special_tokens", 0) if cfg.special_tokens else 0',
     'specials = getattr(encode, "num_special_tokens", 0)'),
    ("F6 flag ignored: specials never counted", "partA/fertility_v1.py",
     'specials = getattr(encode, "num_special_tokens", 0) if cfg.special_tokens else 0', "specials = 0"),
    ("tiktoken claims 2 special tokens", "partA/fertility_v1.py",
     "encode.num_special_tokens = 0  # tiktoken", "encode.num_special_tokens = 2  # tiktoken"),
    ("HF special count off by one", "partA/fertility_v1.py",
     "tok.num_special_tokens_to_add(pair=False)", "tok.num_special_tokens_to_add(pair=False) + 1"),
    ("F7 denominator ignored (always words)", "partA/fertility_v1.py",
     "n_words = count_units(line, cfg.denominator, cfg)", "n_words = count_words(line, cfg)"),
    ("F7 sentence unit counts 2 per line", "partA/fertility_v1.py",
     "# each line is one parallel sentence\n        return 1", "# each line is one parallel sentence\n        return 2"),
    ("V1 keeps word denominator", "partA/fertility_v1.py", 'aggregate="total", denominator="sentence")', 'aggregate="total", denominator="words")'),
    ("F8 char unit ignored (always code points)", "partA/fertility_v1.py",
     "n_chars = count_units(line, cfg.char_unit, cfg)", "n_chars = len(line)"),
    ("F8 graphemes counted as code points", "partA/fertility_v1.py", "return count_graphemes(text)", "return len(text)"),
    ("F8 bytes counted as code points", "partA/fertility_v1.py", "return count_bytes(text)", "return len(text)"),
    ("blank lines no longer skipped", "partA/fertility_v1.py",
     "for line in (raw.strip() for raw in f) if line]", "for line in (raw.strip() for raw in f)]"),
    ("V1 equals V0", "partA/fertility_v1.py", 'V1 = replace(V0, split="whitespace", lowercase=False, aggregate="total", denominator="sentence")', "V1 = V0"),
    ("--v0 base ignored", "partA/fertility_v1.py", "base = V0 if args.v0 else V1", "base = V1"),
    ("CLI fix flags ignored", "partA/fertility_v1.py", "return replace(base, **overrides)", "return base"),
    ("delta sign flipped", "partA/audit/experiments.py",
     "(after[corpus][lang][k] - v) / v * 100", "(v - after[corpus][lang][k]) / v * 100"),
    ("threshold < becomes <=", "partA/audit/experiments.py", "abs(d) < THRESHOLD_PCT", "abs(d) <= THRESHOLD_PCT"),
    ("fertility ratio uses tok/char", "partA/audit/experiments.py",
     'r["fertility"] / res["eng"]["fertility"]', 'r["tok_per_char"] / res["eng"]["tok_per_char"]'),
    ("lines_changed never counts", "partA/audit/experiments.py",
     'encode, after_cfg)\n    return out\n', 'encode, after_cfg)\n    return {k: 0 for k in out}\n'),
    ("token-line count uses any-metric", "partA/audit/experiments.py",
     'out["tokens"] += v1.count_tokens(mx, encode, before_cfg) != v1.count_tokens(my, encode, after_cfg)',
     'out["tokens"] += v1.analyze([x], encode, before_cfg) != v1.analyze([y], encode, after_cfg)'),
    ("measured_text ignores lowercase flag", "partA/fertility_v1.py",
     "return line.lower() if cfg.lowercase else line", "return line.lower()"),
    ("FLORES drops devtest", "partA/audit/experiments.py", '+ v1.read_raw_lines(FLORES / f"{code}.devtest.txt")', ""),
    ("F1 variant equals v0", "partA/audit/experiments.py", '"F1": v1.replace(v1.V0, split="whitespace"),', '"F1": v1.V0,'),
    ("own-metrics verdict uses ratios too", "partA/audit/experiments.py", "threshold_verdict({k: m[k] for k in own})", "threshold_verdict(m)"),
    ("F9 compares tokenizer a with itself", "partA/audit/experiments.py",
     "a, b = measure(cfg, encode_a, corpora), measure(cfg, encode_b, corpora)",
     "a, b = measure(cfg, encode_a, corpora), measure(cfg, encode_a, corpora)"),
    ("F9 registry points at XLM-R", "partA/audit/experiments.py",
     'TOKENIZER_FINDINGS = {"F9": ("gpt2", LLAMA)}', 'TOKENIZER_FINDINGS = {"F9": ("gpt2", XLMR)}'),
    ("ablation leave-one-out keeps the V1 value", "partA/audit/ablation.py",
     "{f: getattr(v1.V0, f)}) for k, f in V1_FIXES.items()}", "{f: getattr(v1.V1, f)}) for k, f in V1_FIXES.items()}"),
    ("ablation cumulative adds v0 values", "partA/audit/ablation.py",
     "cfg = v1.replace(cfg, **{f: getattr(v1.V1, f)})", "cfg = v1.replace(cfg, **{f: getattr(v1.V0, f)})"),
    ("ablation contribution sign flipped", "partA/audit/ablation.py",
     '"delta_pct_v1_vs_without": pct(full, m)', '"delta_pct_v1_vs_without": pct(m, full)'),
    ("report drops the F8 tok/char tables", "partA/audit/report.py", 'if name.startswith("F8"):', "if False:"),
    ("report shows tok/char ratio as the instrument ratio", "partA/audit/report.py",
     "| {r['b'][corpus][lang]['fertility_ratio_vs_eng']:.3f} ", "| {r['b'][corpus][lang]['tok_per_char_ratio_vs_eng']:.3f} "),
    ("missing Llama never reported", "partA/testsupport.py",
     "        v1.load_tokenizer(LLAMA)\n    except Exception as exc:", "        pass\n    except Exception as exc:"),
    ("v0 SHA-256 guard disabled", "partA/audit/v0.py", "if got != V0_SHA256:", "if False:"),
    ("F5 tech debt reintroduced in v1", "partA/fertility_v1.py",
     "import argparse\n", "import argparse\nimport random\n\nrandom.seed(1337)\n"),
    ("v1 line order depends on RNG", "partA/fertility_v1.py",
     "        return [line for line in (raw.strip() for raw in f) if line]",
     "        import random\n        out = [line for line in (raw.strip() for raw in f) if line]\n"
     "        random.shuffle(out)\n        return out"),
    ("missing FLORES never reported", "partA/testsupport.py", "if not missing:", "if True:"),
    ("skip logic inverted (skips when present)", "partA/tests/conftest.py",
     "and (reason := check()):", "and not (reason := check()):\n            reason = 'mutant'"),
]


def run_tests(cwd: Path, tests=TESTS) -> tuple[int, int]:
    # child writes UTF-8 and we decode UTF-8 regardless of the OS locale (cp1252 on
    # Windows crashed on Indic text in assertion output, e.g. byte 0x81 of U+0941)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, "-m", "pytest", *tests, "-q", "-p", "no:cacheprovider"],
                       cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
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
