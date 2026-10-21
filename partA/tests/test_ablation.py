"""A2 ablation: leave-one-out from fully corrected V1, then the cumulative path from v0.

Scenarios use fake tokenizers so the configs and numbers are checkable by hand.
"""
import pytest


def one_token_per_letter(s):
    return [c for c in s if not c.isspace()]


def test_given_v1_then_ablated_fixes_are_exactly_the_fields_where_v1_differs_from_v0():
    from audit.ablation import V1_FIXES

    # F4 (nfc) and F6 (special tokens) are "fine as written": V1 keeps v0's value
    assert V1_FIXES == {"F1": "split", "F3": "lowercase", "F2": "aggregate", "F7": "denominator"}


def test_given_leave_one_out_then_each_config_reverts_exactly_one_fix_from_v1():
    from dataclasses import fields

    import fertility_v1 as v1
    from audit.ablation import leave_one_out_configs

    configs = leave_one_out_configs()
    assert set(configs) == {"F1", "F3", "F2", "F7"}
    for name, cfg in configs.items():
        diff = [f.name for f in fields(v1.Config) if getattr(cfg, f.name) != getattr(v1.V1, f.name)]
        assert len(diff) == 1 and getattr(cfg, diff[0]) == getattr(v1.V0, diff[0]), name


def test_given_cumulative_path_then_it_starts_at_v0_adds_one_fix_per_step_and_ends_at_v1():
    import fertility_v1 as v1
    from audit.ablation import cumulative_configs

    steps = cumulative_configs()
    assert [name for name, _ in steps] == ["v0", "+F1", "+F3", "+F2", "+F7"]
    assert steps[0][1] == v1.V0 and steps[-1][1] == v1.V1


@pytest.mark.flores
@pytest.mark.gpt2
@pytest.mark.llama
def test_given_committed_ablation_when_rebuilt_then_identical():
    """Staleness guard: ablation.json must equal a fresh rebuild on all three tokenizers."""
    import json

    from audit.ablation import OUT, build

    assert json.loads(json.dumps(build())) == json.loads(OUT.read_text(encoding="utf-8"))


def test_given_v1_then_f1_and_f2_are_subsumed_by_the_sentence_denominator():
    """Ablation finding pinned by hand: with denominator='sentence', word splitting is
    unused and each line's denominator is 1, so line_mean == total exactly."""
    import fertility_v1 as v1

    lines = ["ab  cd", "abcdef ghi", "a"]
    full = v1.analyze(lines, one_token_per_letter, v1.V1)["fertility"]
    for field, v0_value in (("split", "space"), ("aggregate", "line_mean")):
        assert v1.analyze(lines, one_token_per_letter, v1.replace(v1.V1, **{field: v0_value}))["fertility"] == full


def test_given_fake_corpus_when_ablating_then_numbers_match_direct_measurement():
    import fertility_v1 as v1
    from audit.ablation import run_ablation
    from audit.experiments import measure

    corpora = {"toy": {"eng": ["ab cd", "Ef"], "hin": ["abcdef", "a  b"]}}
    res = run_ablation(one_token_per_letter, corpora)
    assert res["v1"] == measure(v1.V1, one_token_per_letter, corpora)
    without_f1 = measure(v1.replace(v1.V1, split="space"), one_token_per_letter, corpora)
    assert res["leave_one_out"]["F1"]["metrics"] == without_f1
    # contribution = (V1 - V1 without fix) / (V1 without fix), per metric
    r = res["leave_one_out"]["F1"]["delta_pct_v1_vs_without"]["toy"]["hin"]["fertility_ratio_vs_eng"]
    a, b = res["v1"]["toy"]["hin"]["fertility_ratio_vs_eng"], without_f1["toy"]["hin"]["fertility_ratio_vs_eng"]
    assert r == pytest.approx((a - b) / b * 100)
    assert [s["step"] for s in res["cumulative"]] == ["v0", "+F1", "+F3", "+F2", "+F7"]
    assert res["cumulative"][0]["metrics"] == measure(v1.V0, one_token_per_letter, corpora)
