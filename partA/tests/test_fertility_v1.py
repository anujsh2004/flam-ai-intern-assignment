"""fertility_v1.py: corrected script with one flag per audited fix.

Step 4 scenario: Given --v0 settings, when v1 analyzes any corpus, then it
returns exactly the original script's numbers (so every later delta is
caused only by the flag being changed).
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOY = ROOT / "starter_kit" / "corpus_sample"
FLORES = ROOT / "partA" / "corpus" / "prepared"

CORPORA = [TOY / "eng_sample.txt", TOY / "hin_sample.txt"] + [
    FLORES / f"{lang}.{split}.txt"
    for lang in ("eng_Latn", "hin_Deva", "kan_Knda", "tam_Taml")
    for split in ("dev", "devtest")
]


@pytest.fixture(scope="module")
def v0():
    from audit.v0 import load_v0

    return load_v0()


@pytest.fixture(scope="module")
def gpt2(v0):
    return v0.load_tokenizer("gpt2")


@pytest.mark.parametrize("path", CORPORA, ids=lambda p: p.name)
def test_given_v0_config_when_analyzing_then_identical_to_original(path, v0, gpt2):
    import fertility_v1 as v1

    original = v0.analyze(v0.read_lines(str(path)), gpt2)
    got = v1.analyze(v1.read_lines(path, v1.V0), gpt2, v1.V0)
    assert (got["fertility"], got["tok_per_char"]) == original  # exact, not approx


def one_token_per_word(s):
    """Fake tokenizer: one token per real (whitespace-delimited) word."""
    return s.split()


def test_f1_given_double_space_when_split_on_space_then_empty_word_inflates_denominator():
    import fertility_v1 as v1

    # "a  b".split(" ") -> ["a", "", "b"]: 2 tokens / 3 "words"
    assert v1.analyze(["a  b"], one_token_per_word, v1.V0)["fertility"] == pytest.approx(2 / 3)


def test_f1_given_whitespace_split_when_double_space_then_only_real_words_count():
    import fertility_v1 as v1

    cfg = v1.replace(v1.V0, split="whitespace")
    assert v1.analyze(["a  b"], one_token_per_word, cfg)["fertility"] == pytest.approx(1.0)


def cfg_for(*argv):
    import fertility_v1 as v1

    return v1.config_from_args(v1.build_parser().parse_args(["--corpus", "x=y", *argv]))


def test_given_v1_constant_then_it_is_the_single_source_of_corrected_defaults():
    import fertility_v1 as v1

    assert v1.V1 == v1.replace(v1.V0, split="whitespace")
    assert cfg_for() == v1.V1  # CLI with no fix flags = fully corrected


def test_given_v0_with_a_fix_flag_then_v0_is_the_base_and_the_flag_overrides():
    import fertility_v1 as v1

    assert cfg_for("--v0") == v1.V0
    assert cfg_for("--v0", "--split", "whitespace") == v1.replace(v1.V0, split="whitespace")
    assert cfg_for("--split", "space") == v1.replace(v1.V1, split="space")


def test_f1_given_cli_split_flag_then_config_uses_it():
    import fertility_v1 as v1

    assert v1.config_from_args(v1.build_parser().parse_args(["--corpus", "x=y", "--split", "whitespace"])).split == "whitespace"
    assert v1.config_from_args(v1.build_parser().parse_args(["--corpus", "x=y", "--v0"])) == v1.V0


PASTED = "First line here.\n\n   \n\tSecond  line.\n\n"  # blank, whitespace-only, tab, double space


def test_given_pasted_text_with_blank_lines_when_read_then_they_are_skipped(tmp_path):
    """Our corpora have no blank lines (measured), but pasted defense input may.
    A blank line must never reach analyze(): "".split() has 0 words -> ZeroDivisionError."""
    import fertility_v1 as v1

    p = tmp_path / "pasted.txt"
    p.write_text(PASTED, encoding="utf-8")
    lines = v1.read_raw_lines(p)
    assert lines == ["First line here.", "Second  line."]
    fixed = v1.replace(v1.V0, split="whitespace")
    assert v1.analyze(lines, one_token_per_word, fixed)["fertility"] == pytest.approx(1.0)


def test_given_pasted_text_when_run_with_v0_then_matches_original_cli(tmp_path):
    p = tmp_path / "pasted.txt"
    p.write_text(PASTED, encoding="utf-8")
    args = ["--corpus", f"eng={TOY / 'eng_sample.txt'}", "--corpus", f"x={p}", "--tokenizer", "gpt2"]

    def run(script, *extra):
        return subprocess.run([sys.executable, str(script), *args, *extra],
                              capture_output=True, text=True, encoding="utf-8", check=True).stdout

    assert run(ROOT / "partA" / "fertility_v1.py", "--v0") == run(ROOT / "starter_kit" / "fertility.py")


def test_given_v0_flag_when_run_as_cli_then_stdout_matches_original_byte_for_byte():
    args = ["--corpus", f"eng={TOY / 'eng_sample.txt'}", "--corpus", f"hin={TOY / 'hin_sample.txt'}",
            "--tokenizer", "gpt2"]

    def run(script, *extra):
        return subprocess.run([sys.executable, str(script), *args, *extra],
                              capture_output=True, text=True, encoding="utf-8", check=True).stdout

    assert run(ROOT / "partA" / "fertility_v1.py", "--v0") == run(ROOT / "starter_kit" / "fertility.py")
