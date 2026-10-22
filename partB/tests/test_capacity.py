"""Part B: capacity reconciliation (partB/capacity.py). Expected values derived by hand
from bench/model_spec.md and bench/bench_log.csv."""
import pytest


def test_given_original_bench_log_when_loaded_then_13_typed_rows():
    from capacity import load_bench

    rows = load_bench()
    assert len(rows) == 13
    assert rows[0] == {"batch_size": 1, "prompt_len": 512, "gen_len": 256, "num_requests": 1, "wall_clock_s": 10.94,
                       "reported_tok_s": 70.2, "ttft_ms_p50": 71.1, "itl_ms_p50": 43.48, "e2e_ms_p95": 12863.7,
                       "preempted_seqs": 0, "kv_cache_util": 0.01}
    assert rows[-1]["batch_size"] == 48 and rows[-1]["preempted_seqs"] == 23


def test_given_spec_constants_then_each_value_appears_in_model_spec_md():
    """The constants are copied from bench/model_spec.md; guard against a typo."""
    from capacity import ROOT, SPEC

    text = (ROOT / "starter_kit" / "bench" / "model_spec.md").read_text(encoding="utf-8")
    for needle in ("| layers | 28 |", "| KV heads (GQA) | 8 |", "| head_dim | 128 |", "| parameters | 4.2 B |",
                   "| KV cache precision | fp16 |", "| weights precision | fp16 |", "1× NVIDIA L4 (24 GB)",
                   "| `max_model_len` | 4096 |", "| `gpu_memory_utilization` | 0.92 |", "assume ~1.6 GB"):
        assert needle in text, needle
    assert SPEC == {"layers": 28, "kv_heads": 8, "head_dim": 128, "params": 4.2e9, "bytes_per_elem": 2,
                    "gpu_gb": 24, "gpu_memory_utilization": 0.92, "overhead_gb": 1.6, "max_model_len": 4096}


def test_b1_kv_bytes_per_token_is_exact():
    from capacity import SPEC, kv_bytes_per_token

    assert kv_bytes_per_token(SPEC) == 2 * 28 * 8 * 128 * 2 == 114_688  # K and V, fp16


def test_b1_bytes_per_4096_token_sequence():
    from capacity import SPEC, seq_bytes

    assert seq_bytes(SPEC) == 114_688 * 4096 == 469_762_048


def test_b1_max_concurrent_sequences_under_both_conventions():
    from capacity import SPEC, max_concurrent

    # decimal: 24e9*0.92 - 4.2e9*2 - 1.6e9 = 12.08e9 bytes for KV
    assert max_concurrent(SPEC, "decimal") == pytest.approx(12.08e9 / 469_762_048)  # 25.715
    # binary: 24 GiB*0.92 - 8.4e9 (weights are a byte count) - 1.6 GiB
    assert max_concurrent(SPEC, "binary") == pytest.approx((24 * 2**30 * 0.92 - 8.4e9 - 1.6 * 2**30) / 469_762_048)


def test_b1_log_check_capacity_implied_by_cache_utilisation_at_non_preempting_rows():
    """batch*(prompt+gen) tokens resident at peak / util = KV capacity in tokens. util is
    rounded to 2 decimals, so each row gives an interval from util +/- 0.005."""
    from capacity import load_bench, util_implied_capacity

    caps = util_implied_capacity(load_bench())
    b24 = next(c for c in caps if c["batch_size"] == 24 and c["prompt_len"] == 3584)
    assert b24["tokens_resident"] == 24 * 4096
    assert b24["capacity_tokens"] == pytest.approx(98_304 / 0.93)
    assert (b24["lo"], b24["hi"]) == pytest.approx((98_304 / 0.935, 98_304 / 0.925))
    assert all(c["preempted_seqs"] == 0 for c in caps)


def test_b1_log_check_sequences_that_fit_at_preempting_rows():
    from capacity import fit_from_preemption, load_bench

    assert fit_from_preemption(load_bench()) == [{"batch_size": 32, "preempted_seqs": 7, "fit": 25},
                                                 {"batch_size": 48, "preempted_seqs": 23, "fit": 25}]


def test_b1_the_log_decides_the_convention_decimal_gb():
    """D-09: both log checks agree with decimal GB and rule out binary GiB."""
    import math

    from capacity import SPEC, convention_check, fit_from_preemption, kv_budget_bytes, kv_bytes_per_token, load_bench

    rows = load_bench()
    chk = convention_check(rows, SPEC)
    lo, hi = chk["util_interval_tokens"]
    dec = kv_budget_bytes(SPEC, "decimal") / kv_bytes_per_token(SPEC)  # 105,329 tokens
    binary = kv_budget_bytes(SPEC, "binary") / kv_bytes_per_token(SPEC)  # 118,497 tokens
    assert lo <= dec <= hi and not lo <= binary <= hi
    assert {f["fit"] for f in fit_from_preemption(rows)} == {math.floor(chk["max_concurrent"]["decimal"])}
    assert chk["supported"] == "decimal"


def test_b3_reported_tok_s_counts_prompt_and_generated_tokens_on_every_row():
    """The misread column: reported_tok_s = (prompt + gen) * requests / wall, within the log's
    rounding (1 decimal on the rate, 2 on wall-clock). Generated-only fails on every row."""
    from capacity import identify_reported_formula, load_bench

    res = identify_reported_formula(load_bench())
    assert res["prompt_plus_gen"]["rows_matching"] == 13
    assert res["gen_only"]["rows_matching"] == 0


def test_b3_e2e_p95_exceeds_the_run_wall_clock_on_12_of_13_rows():
    """Log-quality observation: with all requests submitted at once, no request can outlast the
    run, so the latency columns and wall_clock_s cannot share a start point."""
    from capacity import load_bench, timing_inconsistency

    rows = timing_inconsistency(load_bench())
    assert sum(r["e2e_p95_exceeds_wall"] for r in rows) == 12
    b1 = rows[0]
    assert (b1["batch_size"], b1["wall_s"], b1["e2e_p95_s"]) == (1, 10.94, pytest.approx(12.8637))


def row(rows, batch, prompt):
    return next(r for r in rows if r["batch_size"] == batch and r["prompt_len"] == prompt)


def test_b3_goodput_of_batch24_long_row_two_independent_ways_agree():
    """User choice B: (1) generated tokens / wall clock; (2) the separately logged reported
    column scaled to generated tokens. Agreement within the log's rounding."""
    from capacity import goodput_two_ways, load_bench

    g = goodput_two_ways(row(load_bench(), 24, 3584))
    assert g["from_wall_clock"] == pytest.approx(24 * 512 / 61.16)  # 200.92 tok/s
    assert g["from_reported_column"] == pytest.approx(1607.4 * 512 / (3584 + 512))  # 200.93 tok/s
    assert abs(g["from_wall_clock"] - g["from_reported_column"]) < 0.05 * 512 / 4096 + 0.02


def test_b3_latency_column_estimates_only_bracket_the_goodput():
    from capacity import goodput_bounds, load_bench

    b = goodput_bounds(row(load_bench(), 24, 3584))
    assert b["from_p50_ttft_itl"] == pytest.approx(24 * 512 / ((500.5 + 511 * 96.07) / 1000))  # ~247.8 (b24 TTFT 500.5)
    assert b["from_e2e_p95"] == pytest.approx(24 * 512 / 69.2213)  # ~177.5
    assert b["from_e2e_p95"] < 24 * 512 / 61.16 < b["from_p50_ttft_itl"]


def test_b3_longer_prompts_give_lower_goodput_at_every_shared_batch_size():
    """Refutes REPORT_v0: 'long prompts hit 1311 tok/s vs 883' compares reported columns that
    count prompt tokens. Useful (generated) tokens per second are lower for long prompts."""
    from capacity import goodput, load_bench

    rows = load_bench()
    for b in (4, 8, 16, 32):
        assert goodput(row(rows, b, 3584)) < goodput(row(rows, b, 512)), b
    assert goodput(row(rows, 16, 512)) == pytest.approx(16 * 256 / 13.91)  # 294.4
    assert goodput(row(rows, 16, 3584)) == pytest.approx(16 * 512 / 49.97)  # 163.9


def test_b3_batch48_delivers_far_below_3200_and_below_batch24():
    from capacity import goodput, load_bench

    rows = load_bench()
    b48, b24 = row(rows, 48, 3584), row(rows, 24, 3584)
    assert b48["reported_tok_s"] == 1298.5  # even the inflated column falls, not 3200
    assert goodput(b48) == pytest.approx(48 * 512 / 151.41)  # ~162.3 useful tok/s
    assert goodput(b48) < goodput(b24)


def test_b2_long_sweep_goodput_peaks_at_24_then_falls_exactly_when_preemption_starts():
    from capacity import anomaly, load_bench

    a = anomaly(load_bench())
    assert a["peak_batch"] == 24
    assert [s["batch_size"] for s in a["after_peak"]] == [32, 48]
    assert all(s["preempted_seqs"] > 0 and s["kv_cache_util"] >= 0.97 for s in a["after_peak"])
    assert all(s["preempted_seqs"] == 0 for s in a["up_to_peak"])


def test_b2_option_a_cap_at_logged_non_preempting_batch_runs_48_as_two_waves():
    """Prediction grounded in a logged row: 48 requests = 2 waves of the observed b24 run."""
    from capacity import load_bench, option_a_cap

    p = option_a_cap(load_bench(), requests=48, cap=24)
    assert p["waves"] == 2 and p["wall_s"] == pytest.approx(2 * 61.16)
    assert p["goodput"] == pytest.approx(48 * 512 / (2 * 61.16))  # ~200.9 vs 162.3 observed
    assert p["vs_observed_pct"] == pytest.approx((p["goodput"] / (48 * 512 / 151.41) - 1) * 100)


def test_b2_option_b_fp8_kv_halves_bytes_so_48_fit_and_wall_is_extrapolated():
    """fp8 KV -> 1 byte/elem -> 57,344 B/token -> 51.4 seqs: batch 48 fits. Wall clock at 48 is a
    least-squares line through the non-preempting long rows (b4..b24): an extrapolation."""
    from capacity import SPEC, load_bench, option_b_fp8

    p = option_b_fp8(load_bench(), SPEC, requests=48)
    assert p["kv_bytes_per_token"] == 57_344
    assert p["max_concurrent"] == pytest.approx(12.08e9 / (57_344 * 4096))  # ~51.4
    xs, ys = [4, 8, 16, 24], [28.98, 36.3, 49.97, 61.16]
    mx, my = sum(xs) / 4, sum(ys) / 4
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    assert p["wall_s"] == pytest.approx(my + slope * (48 - mx))  # ~100.5 s
    assert p["goodput"] == pytest.approx(48 * 512 / p["wall_s"])


def test_b2_option_c_lower_max_model_len_cannot_help_this_workload():
    """Paged KV capacity is in tokens, so max_model_len changes neither bytes/token nor capacity;
    every long request is 3584 + 512 = 4096 tokens, so a lower limit would reject them."""
    from capacity import SPEC, load_bench, option_c_max_model_len

    p = option_c_max_model_len(load_bench(), SPEC, new_max=2048)
    assert p["capacity_tokens_unchanged"] is True
    assert p["long_requests_rejected"] == 48 and p["goodput"] == 0


def test_given_crlf_csv_when_loaded_then_no_carriage_returns_leak_into_values(tmp_path):
    from capacity import load_bench

    p = tmp_path / "log.csv"
    p.write_bytes(b"batch_size,prompt_len,gen_len,num_requests,wall_clock_s,reported_tok_s,ttft_ms_p50,"
                  b"itl_ms_p50,e2e_ms_p95,preempted_seqs,kv_cache_util\r\n1,512,256,1,10.94,70.2,71.1,43.48,"
                  b"12863.7,0,0.01\r\n")
    (row,) = load_bench(p)
    assert row["kv_cache_util"] == 0.01 and isinstance(row["preempted_seqs"], int)
