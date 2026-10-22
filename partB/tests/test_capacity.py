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


def test_given_crlf_csv_when_loaded_then_no_carriage_returns_leak_into_values(tmp_path):
    from capacity import load_bench

    p = tmp_path / "log.csv"
    p.write_bytes(b"batch_size,prompt_len,gen_len,num_requests,wall_clock_s,reported_tok_s,ttft_ms_p50,"
                  b"itl_ms_p50,e2e_ms_p95,preempted_seqs,kv_cache_util\r\n1,512,256,1,10.94,70.2,71.1,43.48,"
                  b"12863.7,0,0.01\r\n")
    (row,) = load_bench(p)
    assert row["kv_cache_util"] == 0.01 and isinstance(row["preempted_seqs"], int)
