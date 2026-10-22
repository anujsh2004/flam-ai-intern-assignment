"""A3: tokenization premium vs English (partA/analysis/premium.py).

Hand-derived scenarios; real-tokenizer checks are marked for skip on fresh clones.
"""
import pytest

ENG = [{"tokens": 2, "words": 1, "sentence": 1}, {"tokens": 4, "words": 2, "sentence": 1}]
HIN = [{"tokens": 3, "words": 3, "sentence": 1}, {"tokens": 9, "words": 3, "sentence": 1}]


def test_given_rows_when_premium_per_word_then_ratio_of_per_unit_totals():
    from analysis.premium import premium

    # (12 tokens / 6 words) / (6 tokens / 3 words) = 2 / 2
    assert premium(HIN, ENG, "words") == pytest.approx(1.0)


def test_given_rows_when_premium_per_sentence_then_ratio_of_token_totals():
    from analysis.premium import premium

    # same content, same sentence count: 12 / 6. Same tokens, different denominator -> different answer
    assert premium(HIN, ENG, "sentence") == pytest.approx(2.0)


def test_given_per_request_overhead_when_premium_then_overhead_added_to_every_sentence():
    from analysis.premium import premium

    # one request per sentence, 1 BOS token each: (12 + 2) / (6 + 2)
    assert premium(HIN, ENG, "sentence", overhead=1) == pytest.approx(1.75)


def test_given_constant_premium_when_bootstrapped_then_interval_collapses():
    from analysis.premium import bootstrap_premium

    eng = [{"tokens": t, "sentence": 1} for t in (1, 2, 3, 4)]
    hin = [{"tokens": 2 * t, "sentence": 1} for t in (1, 2, 3, 4)]
    point, lo, hi = bootstrap_premium(hin, eng, "sentence", ["a", "a", "b", "c"], n_boot=300, seed=0)
    assert (point, lo, hi) == pytest.approx((2.0, 2.0, 2.0))


def test_given_sentence_unit_when_bootstrapped_then_equals_a1_clustered_bootstrap():
    """Cross-check against A1's independently tested units.cluster_bootstrap_ratio."""
    from analysis.premium import bootstrap_premium
    from units import cluster_bootstrap_ratio

    eng_t, hin_t = [5, 3, 8, 2, 7, 4], [9, 4, 20, 3, 15, 6]
    clusters = ["a", "a", "b", "b", "c", "d"]
    eng = [{"tokens": t, "sentence": 1} for t in eng_t]
    hin = [{"tokens": t, "sentence": 1} for t in hin_t]
    assert bootstrap_premium(hin, eng, "sentence", clusters, n_boot=500, seed=3) == pytest.approx(
        cluster_bootstrap_ratio(hin_t, eng_t, clusters, n_boot=500, seed=3))


def test_given_per_sentence_premiums_when_summarised_then_linear_percentiles():
    from analysis.premium import spread

    eng = [{"tokens": 1}] * 5
    hin = [{"tokens": t} for t in (1, 2, 3, 4, 5)]
    # linear interpolation (numpy default): p10 = 1 + 0.4*(2-1), p90 = 4 + 0.6*(5-4)
    assert spread(hin, eng) == pytest.approx({"median": 3.0, "p10": 1.4, "p90": 4.6})


def test_given_line_when_tabulated_then_counts_follow_v1_preparation():
    import fertility_v1 as v1
    from analysis.premium import sentence_table

    rows = sentence_table(lambda s: s.split(), ["Ab  cd", "ज़"], v1.V1)
    # V1: no lowercasing, NFC (U+095B -> 2 code points), whitespace words
    assert rows[0] == {"tokens": 2, "words": 2, "codepoints": 6, "graphemes": 6, "bytes": 6, "sentence": 1}
    assert rows[1]["codepoints"] == 2 and rows[1]["graphemes"] == 1 and rows[1]["bytes"] == 6


def test_registry_lists_four_pinned_tokenizers_incl_indicbert():
    from analysis.premium import TOKENIZERS
    from audit.experiments import INDICBERT, LLAMA, XLMR

    assert TOKENIZERS == {"gpt2": "gpt2", "llama": LLAMA, "xlmr": XLMR, "indicbert": INDICBERT}
    assert INDICBERT == "hf:ai4bharat/IndicBERTv2-MLM-only@8598f13fe52443bc3fc054fcd665944560145b5c"


@pytest.mark.flores
def test_given_flores_when_articles_loaded_then_one_id_per_sentence_and_562_articles():
    from analysis.premium import article_ids

    ids = article_ids()
    assert len(ids) == 2009 and len(set(ids)) == 562  # A1: 281 + 281 articles


@pytest.mark.flores
def test_given_indicbert_when_tokenizing_flores_then_no_unknown_tokens():
    """An Indic-aware tokenizer that mapped text to [UNK] would look falsely cheap."""
    from transformers import AutoTokenizer

    import fertility_v1 as v1
    from audit.experiments import INDICBERT, load_corpora

    _, name, rev = v1.parse_tokenizer_spec(INDICBERT)
    tok = AutoTokenizer.from_pretrained(name, revision=rev)
    for lang, lines in load_corpora()["flores"].items():
        ids = [i for line in lines[:300] for i in tok.encode(line, add_special_tokens=False)]
        assert tok.unk_token_id not in ids, lang
