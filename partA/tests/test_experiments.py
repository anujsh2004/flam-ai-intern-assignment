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
    assert res["lines_changed"]["toy"] == {"eng": 0, "hin": 0}


def test_given_f1_variant_when_compared_then_delta_and_changed_lines_are_exact():
    import fertility_v1 as v1
    from audit.experiments import compare

    res = compare(v1.V0, v1.replace(v1.V0, split="whitespace"), one_token_per_word, CORPORA)
    # v0 eng: lines "a b" -> 2/2 = 1, "c  d" -> 2/3; mean = 5/6. fixed: mean = 1
    assert res["before"]["toy"]["eng"]["fertility"] == pytest.approx(5 / 6)
    assert res["after"]["toy"]["eng"]["fertility"] == pytest.approx(1.0)
    assert res["delta_pct"]["toy"]["eng"]["fertility"] == pytest.approx(20.0)  # (1 - 5/6) / (5/6)
    assert res["lines_changed"]["toy"] == {"eng": 1, "hin": 0}
    # ratio vs English: hin fertility 1.0 in both; ratio 1/(5/6)=1.2 -> 1/1=1.0
    assert res["before"]["toy"]["hin"]["fertility_ratio_vs_eng"] == pytest.approx(1.2)
    assert res["after"]["toy"]["hin"]["fertility_ratio_vs_eng"] == pytest.approx(1.0)


@pytest.mark.parametrize("deltas,expected", [
    ({"a": 0.99, "b": -0.5}, "negligible"),
    ({"a": 1.0, "b": 0.0}, "material"),
    ({"a": -1.2}, "material"),
])
def test_given_d14_threshold_when_classifying_then_one_percent_is_the_line(deltas, expected):
    from audit.experiments import threshold_verdict

    assert threshold_verdict(deltas) == expected
