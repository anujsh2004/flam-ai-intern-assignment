"""A4 evidence: vocabulary coverage per language x tokenizer (partA/analysis/coverage.py).
A fake byte-level codec makes every number derivable by hand."""
import pytest


def byte_encode(s):
    return list(s.encode("utf-8"))  # one token per UTF-8 byte (pure byte fallback)


def byte_decode(ids):
    return bytes(ids).decode("utf-8", errors="replace")


def test_given_ascii_when_byte_codec_then_one_token_per_codepoint_and_no_fragments():
    from analysis.coverage import coverage_row

    r = coverage_row(["ab c"], byte_encode, byte_decode)
    assert (r["codepoints"], r["tokens"]) == (4, 4)
    assert r["tokens_per_codepoint"] == pytest.approx(1.0) and r["fragment_share"] == 0.0


def test_given_kannada_when_byte_codec_then_three_fragment_tokens_per_character():
    """Each Kannada code point is 3 UTF-8 bytes; a single byte never decodes to a whole character."""
    from analysis.coverage import coverage_row

    r = coverage_row(["ಕನ"], byte_encode, byte_decode)  # ಕನ
    assert (r["codepoints"], r["tokens"]) == (2, 6)
    assert r["tokens_per_codepoint"] == pytest.approx(3.0) and r["fragment_share"] == pytest.approx(1.0)


def test_given_whole_character_tokens_then_not_counted_as_fragments():
    from analysis.coverage import coverage_row

    def char_encode(s):
        return [ord(c) for c in s]

    def char_decode(ids):
        return "".join(chr(i) for i in ids)

    r = coverage_row(["ಕನ"], char_encode, char_decode)
    assert r["tokens_per_codepoint"] == pytest.approx(1.0) and r["fragment_share"] == 0.0


def test_given_rows_then_codepoints_are_reported_relative_to_english():
    from analysis.coverage import relative_to_english

    rows = {"eng": {"codepoints": 100}, "kan": {"codepoints": 105}}
    assert relative_to_english(rows) == {"eng": pytest.approx(1.0), "kan": pytest.approx(1.05)}


def test_given_lines_then_text_is_prepared_as_v1_before_counting():
    """NFC as in V1: precomposed U+095B counts as 2 code points, as A3 measured it."""
    from analysis.coverage import coverage_row

    r = coverage_row(["ज़"], byte_encode, byte_decode)
    assert r["codepoints"] == 2
