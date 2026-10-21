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
    pytest.param(FLORES / f"{lang}.{split}.txt", marks=pytest.mark.flores)
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


@pytest.mark.gpt2
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

    assert v1.V1 == v1.replace(v1.V0, split="whitespace", lowercase=False, aggregate="total")
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


def case_sensitive_tokens(s):
    """Fake tokenizer: each uppercase letter is its own token, each lowercase run one token."""
    import re

    return re.findall(r"[A-Z]|[a-z]+|\S", s)


def test_f3_given_v0_when_text_has_capitals_then_it_measures_lowercased_text():
    import fertility_v1 as v1

    # v0 lowercases first: "nasa x" -> ["nasa", "x"] = 2 tokens / 2 words
    assert v1.analyze(["NASA x"], case_sensitive_tokens, v1.V0)["fertility"] == pytest.approx(1.0)


def test_f3_given_no_lowercase_when_text_has_capitals_then_served_text_is_measured():
    import fertility_v1 as v1

    # served text "NASA x" -> N, A, S, A, x = 5 tokens / 2 words
    cfg = v1.replace(v1.V0, lowercase=False)
    assert v1.analyze(["NASA x"], case_sensitive_tokens, cfg)["fertility"] == pytest.approx(2.5)
    assert v1.analyze(["NASA x"], case_sensitive_tokens, cfg)["tok_per_char"] == pytest.approx(5 / 6)


def test_f3_given_cli_lowercase_flags_then_config_follows():
    import fertility_v1 as v1

    assert v1.V1.lowercase is False and v1.V0.lowercase is True
    assert cfg_for("--v0", "--no-lowercase") == v1.replace(v1.V0, lowercase=False)
    assert cfg_for("--lowercase") == v1.replace(v1.V1, lowercase=True)


def one_token_per_codepoint(s):
    return list(s)


PRECOMPOSED_ZA = "ज़"  # ज़ as one code point, as FLORES Hindi stores it (A1)


def test_f4_given_v0_when_precomposed_nukta_then_nfc_decomposes_it_before_tokenizing():
    import fertility_v1 as v1

    # NFC maps U+095B -> U+091C U+093C (composition exclusion): 2 code points
    assert v1.prepare([PRECOMPOSED_ZA], v1.V0) == ["ज़"]
    assert v1.analyze(v1.prepare([PRECOMPOSED_ZA], v1.V0), one_token_per_codepoint, v1.V0)["fertility"] == 2.0


def test_f4_given_no_nfc_when_precomposed_nukta_then_raw_text_is_tokenized():
    import fertility_v1 as v1

    cfg = v1.replace(v1.V0, nfc=False)
    assert v1.prepare([PRECOMPOSED_ZA], cfg) == [PRECOMPOSED_ZA]
    assert v1.analyze(v1.prepare([PRECOMPOSED_ZA], cfg), one_token_per_codepoint, cfg)["fertility"] == 1.0


def test_f4_given_cli_nfc_flags_then_config_follows_and_v1_keeps_nfc():
    import fertility_v1 as v1

    assert v1.V0.nfc is True and v1.V1.nfc is True  # F4 pre-registered as "fine": V1 keeps it
    assert cfg_for("--no-nfc") == v1.replace(v1.V1, nfc=False)


def one_token_per_letter(s):
    """Fake tokenizer: one token per non-space character."""
    return [c for c in s if not c.isspace()]


# Constructed F2 corpus: a short high-ratio line and longer low-ratio lines.
#   line                    tokens words codepoints  per-line fertility
#   "abcdef"                   6     1       6          6.0
#   "a b c d e f g h i j"     10    10      19          1.0
#   "ab cd ef gh"              8     4      11          2.0
#   totals                    24    15      36
F2_CORPUS = ["abcdef", "a b c d e f g h i j", "ab cd ef gh"]


def test_f2_given_v0_when_averaging_per_line_then_short_lines_dominate():
    import fertility_v1 as v1

    r = v1.analyze(F2_CORPUS, one_token_per_letter, v1.V0)
    assert r["fertility"] == pytest.approx((6 + 1 + 2) / 3)  # 3.0
    assert r["tok_per_char"] == pytest.approx((6 / 6 + 10 / 19 + 8 / 11) / 3)  # ~0.7512


def test_f2_given_totals_when_aggregating_then_ratio_of_sums():
    import fertility_v1 as v1

    r = v1.analyze(F2_CORPUS, one_token_per_letter, v1.replace(v1.V0, aggregate="total"))
    assert r["fertility"] == pytest.approx(24 / 15)  # 1.6
    assert r["tok_per_char"] == pytest.approx(24 / 36)  # 0.6667


def test_f2_given_same_text_split_into_more_lines_then_totals_do_not_change_but_average_does():
    """A cost metric must not depend on where line breaks fall."""
    import fertility_v1 as v1

    resplit = ["abcdef", "a b c d e f g h i j", "ab cd", "ef gh"]
    total = v1.replace(v1.V0, aggregate="total")
    a, b = v1.analyze(F2_CORPUS, one_token_per_letter, total), v1.analyze(resplit, one_token_per_letter, total)
    assert a["fertility"] == pytest.approx(b["fertility"])
    m1, m2 = v1.analyze(F2_CORPUS, one_token_per_letter, v1.V0), v1.analyze(resplit, one_token_per_letter, v1.V0)
    assert m1["fertility"] != pytest.approx(m2["fertility"])  # 3.0 vs (6+1+2+2)/4 = 2.75


def test_f2_given_cli_aggregate_flag_then_config_follows_and_v1_uses_totals():
    import fertility_v1 as v1

    assert v1.V0.aggregate == "line_mean" and v1.V1.aggregate == "total"
    assert cfg_for("--v0", "--aggregate", "total") == v1.replace(v1.V0, aggregate="total")


def with_specials(n):
    """Fake tokenizer that, like XLM-R, would add n special tokens per encoded sequence."""
    def encode(s):
        return s.split()
    encode.num_special_tokens = n
    return encode


def test_f6_given_v0_when_tokenizer_has_specials_then_they_are_not_counted():
    import fertility_v1 as v1

    # "a b" = 2 tokens / 2 words; v0 passes add_special_tokens=False
    assert v1.analyze(["a b"], with_specials(2), v1.V0)["fertility"] == pytest.approx(1.0)


def test_f6_given_special_tokens_on_when_analyzing_then_each_line_gains_them():
    import fertility_v1 as v1

    cfg = v1.replace(v1.V0, special_tokens=True)
    # line_mean: ("a b": (2+2)/2 = 2.0, "a b c d": (4+2)/4 = 1.5) -> 1.75
    assert v1.analyze(["a b", "a b c d"], with_specials(2), cfg)["fertility"] == pytest.approx(1.75)
    # a tokenizer without specials (e.g. tiktoken) is unaffected
    assert v1.analyze(["a b"], one_token_per_word, cfg)["fertility"] == pytest.approx(1.0)


def test_f6_given_cli_flag_then_config_follows_and_both_v0_and_v1_exclude_specials():
    import fertility_v1 as v1

    assert v1.V0.special_tokens is False and v1.V1.special_tokens is False
    assert cfg_for("--v0", "--special-tokens") == v1.replace(v1.V0, special_tokens=True)


@pytest.mark.flores
def test_f6_given_xlmr_when_specials_modelled_as_count_then_matches_real_add_special_tokens():
    """The count model must equal the tokenizer's own add_special_tokens=True output."""
    from transformers import AutoTokenizer

    import fertility_v1 as v1
    from audit.experiments import XLMR

    kind, name, rev = v1.parse_tokenizer_spec(XLMR)
    tok = AutoTokenizer.from_pretrained(name, revision=rev)
    encode = v1.load_tokenizer(XLMR)
    lines = v1.read_raw_lines(FLORES / "kan_Knda.dev.txt")[:200] + v1.read_raw_lines(FLORES / "eng_Latn.dev.txt")[:200]
    for line in lines:
        assert len(tok.encode(line, add_special_tokens=True)) == len(encode(line)) + encode.num_special_tokens


@pytest.mark.gpt2
def test_f6_given_tiktoken_then_no_special_tokens_are_reported():
    import fertility_v1 as v1

    assert v1.load_tokenizer("gpt2").num_special_tokens == 0


@pytest.mark.parametrize("spec,expected", [
    ("gpt2", ("tiktoken", "gpt2", None)),
    ("hf:xlm-roberta-base", ("hf", "xlm-roberta-base", None)),
    ("hf:FacebookAI/xlm-roberta-base@e73636d4f797dec63c3081bb6ed5c7b0bb3f2089",
     ("hf", "FacebookAI/xlm-roberta-base", "e73636d4f797dec63c3081bb6ed5c7b0bb3f2089")),
])
def test_given_tokenizer_spec_when_parsed_then_revision_can_be_pinned(spec, expected):
    import fertility_v1 as v1

    assert v1.parse_tokenizer_spec(spec) == expected


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


@pytest.mark.gpt2
def test_given_pasted_text_when_run_with_v0_then_matches_original_cli(tmp_path):
    p = tmp_path / "pasted.txt"
    p.write_text(PASTED, encoding="utf-8")
    args = ["--corpus", f"eng={TOY / 'eng_sample.txt'}", "--corpus", f"x={p}", "--tokenizer", "gpt2"]

    def run(script, *extra):
        return subprocess.run([sys.executable, str(script), *args, *extra],
                              capture_output=True, text=True, encoding="utf-8", check=True).stdout

    assert run(ROOT / "partA" / "fertility_v1.py", "--v0") == run(ROOT / "starter_kit" / "fertility.py")


@pytest.mark.gpt2
def test_given_v0_flag_when_run_as_cli_then_stdout_matches_original_byte_for_byte():
    args = ["--corpus", f"eng={TOY / 'eng_sample.txt'}", "--corpus", f"hin={TOY / 'hin_sample.txt'}",
            "--tokenizer", "gpt2"]

    def run(script, *extra):
        return subprocess.run([sys.executable, str(script), *args, *extra],
                              capture_output=True, text=True, encoding="utf-8", check=True).stdout

    assert run(ROOT / "partA" / "fertility_v1.py", "--v0") == run(ROOT / "starter_kit" / "fertility.py")
