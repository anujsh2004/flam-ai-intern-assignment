"""Part C back-of-envelope arithmetic (partC/arithmetic.py). Expected values derived by hand
from the stated assumptions; the memo quotes only these generated numbers."""
import pytest


def test_reviewer_capacity_in_the_gpu_window_and_its_sensitivity():
    from arithmetic import ASSUMPTIONS, reviewer_capacity

    assert ASSUMPTIONS["reviewer_hours_per_week"] == 10 and ASSUMPTIONS["gpu_weeks"] == 2
    cap = reviewer_capacity(ASSUMPTIONS)
    assert cap["hours_in_gpu_window"] == 20 and cap["hours_to_launch_review"] == 30
    assert cap["judgements_by_rate"] == {30: 600, 60: 1200, 90: 1800}


def test_reviewer_budget_plan_fits_at_the_planning_rate():
    """At 60/h: week 1 = 600 judgements (calibration 50 + screening 2 prompt variants x 2 langs x
    100 = 400), week 2 = 600 (final eval 2 langs x 200 = 400 + synthetic-pair spot check 200)."""
    from arithmetic import ASSUMPTIONS, budget_plan

    plan = budget_plan(ASSUMPTIONS, rate=60)
    assert plan["week1"] == {"available": 600, "calibration": 50, "screening": 400, "spare": 150}
    assert plan["week2"] == {"available": 600, "final_eval": 400, "synthetic_spot_check": 200, "spare": 0}
    assert budget_plan(ASSUMPTIONS, rate=30)["fits"] is False  # at 30/h the plan must shrink


def test_confidence_interval_half_widths_for_the_thresholds():
    from arithmetic import ci_half_width

    assert ci_half_width(0.70, 200) == pytest.approx(1.96 * (0.7 * 0.3 / 200) ** 0.5)  # ~0.0635
    assert ci_half_width(0.95, 200) == pytest.approx(1.96 * (0.95 * 0.05 / 200) ** 0.5)  # ~0.0302
    assert ci_half_width(0.50, 100) == pytest.approx(0.098, abs=1e-3)  # screening at n=100


def test_sft_token_volume_uses_the_a3_premiums():
    """2,000 pairs per launch language; ~200 English-equivalent tokens per pair, scaled by A3's
    serving-tokenizer premium (hin 2.53, kan 8.87)."""
    from arithmetic import ASSUMPTIONS, sft_volume

    v = sft_volume(ASSUMPTIONS)
    assert v["tokens_per_pair"] == pytest.approx({"hin": 200 * 2.5276513792647695, "kan": 200 * 8.86768121141174})
    assert v["tokens_per_epoch"] == pytest.approx(2000 * 200 * (2.5276513792647695 + 8.86768121141174))
    assert v["tokens_total"] == pytest.approx(v["tokens_per_epoch"] * 3)


def test_lora_training_time_from_a_compute_estimate():
    """6 x params FLOPs per training token (conservative); A100 312 TFLOPS bf16 at 40% MFU."""
    from arithmetic import ASSUMPTIONS, sft_volume, training_time

    t = training_time(ASSUMPTIONS, sft_volume(ASSUMPTIONS)["tokens_total"])
    assert t["tokens_per_s"] == pytest.approx(312e12 * 0.40 / (6 * 4.2e9))  # ~4,952
    assert t["hours"] == pytest.approx(sft_volume(ASSUMPTIONS)["tokens_total"] / t["tokens_per_s"] / 3600)


def test_full_finetune_memory_is_tight_so_lora_is_chosen():
    """bf16 weights + bf16 grads + fp32 Adam m,v + fp32 master = (2+2+8+4) B/param."""
    from arithmetic import ASSUMPTIONS, finetune_memory_gb

    m = finetune_memory_gb(ASSUMPTIONS)
    assert m["full_ft_states_gb"] == pytest.approx(4.2e9 * 16 / 1e9)  # 67.2 GB before activations
    assert m["lora_base_weights_gb"] == pytest.approx(8.4)


def test_rewriter_adds_a_permanent_serving_overhead():
    """Memory-bound decode: cost per generated token ~ parameter bytes read. A 1B rewriter that
    re-generates the reply adds ~1/4.2 of the main model's decode work to every request."""
    from arithmetic import ASSUMPTIONS, rewriter_overhead

    o = rewriter_overhead(ASSUMPTIONS)
    assert o["extra_decode_fraction"] == pytest.approx(1.0 / 4.2)  # ~+24%
    assert o["capacity_loss_fraction"] == pytest.approx(1 - 1 / (1 + 1 / 4.2))  # ~19% fewer requests/GPU


def test_premiums_are_read_from_a3_not_retyped():
    import json

    from arithmetic import A3, premiums

    r = json.loads(A3.read_text(encoding="utf-8"))["by_tokenizer"]["llama"]["premium"]
    assert premiums()["kan"] == r["kan"]["sentence"][0]


def test_given_committed_results_when_rebuilt_then_identical():
    import json

    from arithmetic import OUT, build

    assert json.loads(json.dumps(build())) == json.loads(OUT.read_text(encoding="utf-8"))
