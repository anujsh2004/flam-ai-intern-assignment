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


def test_given_crlf_csv_when_loaded_then_no_carriage_returns_leak_into_values(tmp_path):
    from capacity import load_bench

    p = tmp_path / "log.csv"
    p.write_bytes(b"batch_size,prompt_len,gen_len,num_requests,wall_clock_s,reported_tok_s,ttft_ms_p50,"
                  b"itl_ms_p50,e2e_ms_p95,preempted_seqs,kv_cache_util\r\n1,512,256,1,10.94,70.2,71.1,43.48,"
                  b"12863.7,0,0.01\r\n")
    (row,) = load_bench(p)
    assert row["kv_cache_util"] == 0.01 and isinstance(row["preempted_seqs"], int)
