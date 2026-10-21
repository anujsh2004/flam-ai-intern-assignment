"""Measurement harness for A2 findings (partA/audit/experiments.py).

Scenarios use a fake tokenizer so expected numbers are derivable by hand.
"""
import pytest


def one_token_per_word(s):
    return s.split()


CORPORA = {"toy": {"eng": ["a b", "c  d"], "hin": ["x y z"]}}


def test_given_identical_configs_when_compared_then_every_delta_is_zero():
    import fertility_v1 as v1
    from audit.experiments import compare

    res = compare(v1.V0, v1.V0, one_token_per_word, CORPORA)
    for metrics in res["delta_pct"]["toy"].values():
        assert all(d == 0 for d in metrics.values())
    zero = {"tokens": 0, "words": 0, "any_metric": 0}
    assert res["lines_changed"]["toy"] == {"eng": zero, "hin": zero}


def test_given_f1_variant_when_compared_then_delta_and_changed_lines_are_exact():
    import fertility_v1 as v1
    from audit.experiments import compare

    res = compare(v1.V0, v1.replace(v1.V0, split="whitespace"), one_token_per_word, CORPORA)
    # v0 eng: lines "a b" -> 2/2 = 1, "c  d" -> 2/3; mean = 5/6. fixed: mean = 1
    assert res["before"]["toy"]["eng"]["fertility"] == pytest.approx(5 / 6)
    assert res["after"]["toy"]["eng"]["fertility"] == pytest.approx(1.0)
    assert res["delta_pct"]["toy"]["eng"]["fertility"] == pytest.approx(20.0)  # (1 - 5/6) / (5/6)
    assert res["lines_changed"]["toy"] == {"eng": {"tokens": 0, "words": 1, "any_metric": 1},
                                        "hin": {"tokens": 0, "words": 0, "any_metric": 0}}
    # ratio vs English: hin fertility 1.0 in both; ratio 1/(5/6)=1.2 -> 1/1=1.0
    assert res["before"]["toy"]["hin"]["fertility_ratio_vs_eng"] == pytest.approx(1.2)
    assert res["after"]["toy"]["hin"]["fertility_ratio_vs_eng"] == pytest.approx(1.0)


def test_given_change_in_one_language_only_when_judged_then_verdicts_exist_per_language_and_corpus():
    import fertility_v1 as v1
    from audit.experiments import compare

    res = compare(v1.V0, v1.replace(v1.V0, split="whitespace"), one_token_per_word, CORPORA)
    # eng fertility +20%; hin unchanged. Note hin's ratio vs eng changes (1.2 -> 1.0), so
    # hin is material through its ratio even though its own fertility did not move.
    assert res["threshold_verdict"]["toy"]["overall"] == "material"
    assert res["threshold_verdict"]["toy"]["by_language"] == {"eng": "material", "hin": "material"}
    assert res["threshold_verdict"]["toy"]["by_language_own_metrics"] == {"eng": "material", "hin": "negligible"}


@pytest.mark.flores
def test_given_change_that_only_moves_code_points_then_token_lines_and_any_metric_lines_are_separated():
    """NFC can change len(line) (tok/char's denominator) without changing tokens;
    the audit must not report that as 'tokens changed'."""
    import fertility_v1 as v1
    from audit.experiments import compare

    corpora = {"toy": {"eng": ["a b"], "hin": ["ज़ x"]}}  # precomposed za; NFC adds a code point
    res = compare(v1.V0, v1.replace(v1.V0, nfc=False), one_token_per_word, corpora)
    assert res["lines_changed"]["toy"]["hin"] == {"tokens": 0, "words": 0, "any_metric": 1}
    res = compare(v1.V0, v1.replace(v1.V0, nfc=False), list, corpora)  # one token per code point
    assert res["lines_changed"]["toy"]["hin"] == {"tokens": 1, "words": 0, "any_metric": 1}


def test_given_variant_when_recorded_then_only_fields_differing_from_v0_are_stored():
    """Stable labels: adding a new Config field must not change existing records."""
    import fertility_v1 as v1
    from audit.experiments import result_record

    rec = result_record("F3", "gpt2", v1.replace(v1.V0, lowercase=False), {})
    assert rec["variant"] == {"lowercase": False}


def test_given_real_data_when_corpora_load_then_sizes_match_a1():
    from audit.experiments import load_corpora

    corpora = load_corpora()
    assert {lang: len(lines) for lang, lines in corpora["toy"].items()} == {"eng": 10, "hin": 10}
    assert {lang: len(lines) for lang, lines in corpora["flores"].items()} == {
        "eng": 2009, "hin": 2009, "kan": 2009, "tam": 2009}


def test_given_findings_registry_then_each_variant_differs_from_v0_in_exactly_one_field():
    from dataclasses import fields

    import fertility_v1 as v1
    from audit.experiments import FINDINGS

    for name, cfg in FINDINGS.items():
        diff = [f.name for f in fields(v1.Config) if getattr(cfg, f.name) != getattr(v1.V0, f.name)]
        assert len(diff) == 1, (name, diff)


@pytest.mark.flores
@pytest.mark.gpt2
def test_given_committed_results_when_recomputed_then_identical():
    """Guards against stale or hand-edited evidence (as A1's stats test does)."""
    import json
    from pathlib import Path

    import fertility_v1 as v1
    from audit.experiments import FINDINGS, compare, load_corpora, result_record

    results = sorted((Path(__file__).resolve().parents[1] / "audit" / "results").glob("*.json"))
    assert results, "no committed results found"
    corpora = load_corpora()
    for path in results:
        saved = json.loads(path.read_text(encoding="utf-8"))
        cfg = FINDINGS[saved["finding"]]
        fresh = result_record(saved["finding"], saved["tokenizer"], cfg,
                              compare(v1.V0, cfg, v1.load_tokenizer(saved["tokenizer"]), corpora))
        assert json.loads(json.dumps(fresh)) == saved, path.name


@pytest.mark.parametrize("deltas,expected", [
    ({"a": 0.99, "b": -0.5}, "negligible"),
    ({"a": 1.0, "b": 0.0}, "material"),
    ({"a": -1.2}, "material"),
])
def test_given_d14_threshold_when_classifying_then_one_percent_is_the_line(deltas, expected):
    from audit.experiments import threshold_verdict

    assert threshold_verdict(deltas) == expected
