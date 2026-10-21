"""Text-unit counters used as denominators (A1 corpus stats, reused in A3).

Expected values are worked out by hand from Unicode, not copied from output.
"""
import pytest

from units import cluster_bootstrap_ratio, count_bytes, count_codepoints, count_graphemes, count_words


def test_given_repeated_spaces_when_counting_words_then_no_empty_words():
    # str.split(" ") would give ["a", "", "b"] -> 3; whitespace words are 2
    assert count_words("a  b") == 2
    assert count_words("  leading and trailing  ") == 3


def test_given_devanagari_when_counting_bytes_then_three_bytes_per_codepoint():
    # हि = U+0939 U+093F, each 3 bytes in UTF-8
    assert count_bytes("हि") == 6
    assert count_codepoints("हि") == 2


def test_given_combining_accent_when_counting_graphemes_then_one_user_perceived_char():
    # "cafe" + U+0301 COMBINING ACUTE: 5 code points, 4 graphemes
    assert count_codepoints("café") == 5
    assert count_graphemes("café") == 4


def test_given_vowel_sign_when_counting_graphemes_then_attached_to_consonant():
    # हि (ha + vowel sign i) is one grapheme cluster under any UAX #29 version
    assert count_graphemes("हि") == 1


def test_given_conjunct_when_counting_graphemes_then_uses_unicode_15_1_rules():
    # नमस्ते = न म स ् त े : under Unicode >=15.1 (conjunct rule GB9c) the
    # virama joins स and त -> clusters न | म | स्ते = 3. Older rules give 4.
    # This pins the library behaviour we document in decision D-05.
    assert count_graphemes("नमस्ते") == 3


@pytest.mark.parametrize(
    "script,conjunct,expected",
    [
        ("Devanagari", "क्ष", 1),  # क्ष
        ("Telugu", "క్ష", 1),
        ("Malayalam", "ക്ഷ", 1),
        ("Kannada", "ಕ್ಷ", 2),  # ಕ್ಷ: not covered by GB9c
        ("Tamil", "க்ஷ", 2),  # க்ஷ: pulli is a visible mark
    ],
)
def test_given_ka_virama_ssa_when_counting_graphemes_then_rule_differs_by_script(script, conjunct, expected):
    """Characterisation: the conjunct rule covers some Indic scripts only, so
    grapheme clusters are not a uniform unit across hin/kan/tam (D-05)."""
    assert count_graphemes(conjunct) == expected


def test_given_constant_ratio_when_bootstrapping_then_interval_collapses():
    num = [2.0, 4.0, 6.0, 8.0]
    den = [1.0, 2.0, 3.0, 4.0]
    clusters = ["a", "a", "b", "b"]
    point, lo, hi = cluster_bootstrap_ratio(num, den, clusters, n_boot=200, seed=0)
    assert point == pytest.approx(2.0)
    assert lo == pytest.approx(2.0) and hi == pytest.approx(2.0)


def test_given_same_seed_when_bootstrapping_then_reproducible():
    num, den = [1, 3, 2, 5, 4, 2], [1, 1, 1, 2, 2, 1]
    clusters = ["a", "a", "b", "b", "c", "c"]
    assert cluster_bootstrap_ratio(num, den, clusters, seed=1) == cluster_bootstrap_ratio(num, den, clusters, seed=1)


def test_given_ratio_of_totals_when_bootstrapping_then_point_is_sum_over_sum():
    # ratio of totals (micro) is 10/5 = 2.0, not the mean of per-item ratios
    # (3/1 + 7/4)/2 = 2.375
    point, _, _ = cluster_bootstrap_ratio([3, 7], [1, 4], ["a", "b"], n_boot=50, seed=0)
    assert point == pytest.approx(2.0)
