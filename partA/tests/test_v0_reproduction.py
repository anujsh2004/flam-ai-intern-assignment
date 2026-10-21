"""Step 3 (A2): the unmodified starter_kit/fertility.py must reproduce REPORT_v0.

Scenario: Given the original script, the toy corpus and the gpt2 tokenizer,
when it is run exactly as the report describes, then it prints the report's
table (eng 1.27 / 0.226, hin 7.45 / 1.579) and the 5.89x ratio line.
If this fails, the mismatch itself is an audit finding.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOY = ROOT / "starter_kit" / "corpus_sample"


def test_given_original_module_when_loaded_then_it_is_the_unmodified_file():
    from audit.v0 import V0_PATH, V0_SHA256, load_v0, sha256_of

    assert V0_PATH == ROOT / "starter_kit" / "fertility.py"
    assert sha256_of(V0_PATH) == V0_SHA256  # guards against accidental edits
    mod = load_v0()
    assert callable(mod.analyze) and callable(mod.read_lines)


def test_given_toy_corpus_when_v0_analyzes_then_report_numbers_reproduce():
    from audit.v0 import load_v0

    mod = load_v0()
    encode = mod.load_tokenizer("gpt2")
    eng = mod.analyze(mod.read_lines(str(TOY / "eng_sample.txt")), encode)
    hin = mod.analyze(mod.read_lines(str(TOY / "hin_sample.txt")), encode)
    # REPORT_v0 prints 2 decimals for fertility and 3 for tok/char
    assert (round(eng[0], 2), round(eng[1], 3)) == (1.27, 0.226)
    assert (round(hin[0], 2), round(hin[1], 3)) == (7.45, 1.579)


def test_given_report_command_when_run_as_cli_then_ratio_line_is_589():
    out = subprocess.run(
        [sys.executable, str(ROOT / "starter_kit" / "fertility.py"),
         "--corpus", f"eng={TOY / 'eng_sample.txt'}",
         "--corpus", f"hin={TOY / 'hin_sample.txt'}",
         "--tokenizer", "gpt2"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    assert "hin is 5.89x the fertility of eng (worse tokenization)" in out
