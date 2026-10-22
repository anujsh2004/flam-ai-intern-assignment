#!/usr/bin/env python3
"""Part B: capacity reconciliation from starter_kit/bench/{model_spec.md, bench_log.csv}.

    python partB/capacity.py      # writes partB/results.json

Design pre-registered in docs/plan.md (Phase 5) and D-09. Every number in
partB/answers.md is generated here and checked by tests.
"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BENCH = ROOT / "starter_kit" / "bench" / "bench_log.csv"
INT_COLS = {"batch_size", "prompt_len", "gen_len", "num_requests", "preempted_seqs"}


# copied from starter_kit/bench/model_spec.md (a test checks each value appears there)
SPEC = {"layers": 28, "kv_heads": 8, "head_dim": 128, "params": 4.2e9, "bytes_per_elem": 2,  # fp16 weights and KV
        "gpu_gb": 24, "gpu_memory_utilization": 0.92, "overhead_gb": 1.6, "max_model_len": 4096}
GB = {"decimal": 1e9, "binary": 2**30}  # D-09: report both; the log decides


def load_bench(path: Path = BENCH) -> list[dict]:
    """Typed rows of the load-test log. The original file is CRLF; csv handles it with newline=''."""
    with open(path, encoding="utf-8", newline="") as f:
        return [{k: int(v) if k in INT_COLS else float(v) for k, v in row.items()} for row in csv.DictReader(f)]


def kv_bytes_per_token(spec: dict) -> int:
    """K and V, per layer, per KV head (GQA), head_dim elements each."""
    return 2 * spec["layers"] * spec["kv_heads"] * spec["head_dim"] * spec["bytes_per_elem"]


def seq_bytes(spec: dict, tokens: int | None = None) -> int:
    return kv_bytes_per_token(spec) * (tokens or spec["max_model_len"])


def kv_budget_bytes(spec: dict, convention: str) -> float:
    """GPU memory the serving engine may use, minus weights and non-KV overhead.
    Weights are a byte count (params x bytes), independent of the GB convention."""
    unit = GB[convention]
    weights = spec["params"] * spec["bytes_per_elem"]
    return spec["gpu_gb"] * unit * spec["gpu_memory_utilization"] - weights - spec["overhead_gb"] * unit


def max_concurrent(spec: dict, convention: str) -> float:
    """Approximate number of full max_model_len sequences the KV budget holds."""
    return kv_budget_bytes(spec, convention) / seq_bytes(spec)


def util_implied_capacity(rows: list[dict]) -> list[dict]:
    """At rows without preemption, all batch*(prompt+gen) tokens are resident at peak, so
    capacity = resident / util. util has 2 decimals -> interval from util +/- 0.005."""
    out = []
    for r in rows:
        if r["preempted_seqs"] or r["kv_cache_util"] < 0.1:  # tiny utils are too coarse to invert
            continue
        resident = r["batch_size"] * (r["prompt_len"] + r["gen_len"])
        out.append({"batch_size": r["batch_size"], "prompt_len": r["prompt_len"], "preempted_seqs": 0,
                    "tokens_resident": resident, "capacity_tokens": resident / r["kv_cache_util"],
                    "lo": resident / (r["kv_cache_util"] + 0.005), "hi": resident / (r["kv_cache_util"] - 0.005)})
    return out


def convention_check(rows: list[dict], spec: dict) -> dict:
    """Which GB convention does the log support? A convention passes if its KV capacity (tokens)
    lies inside every util-implied interval AND its floor(max_concurrent) equals every
    batch - preempted at preempting rows."""
    caps = util_implied_capacity(rows)
    lo, hi = max(c["lo"] for c in caps), min(c["hi"] for c in caps)
    fits = {f["fit"] for f in fit_from_preemption(rows)}
    per = {}
    for conv in GB:
        tokens = kv_budget_bytes(spec, conv) / kv_bytes_per_token(spec)
        per[conv] = lo <= tokens <= hi and fits == {int(max_concurrent(spec, conv))}
    passing = [c for c, ok in per.items() if ok]
    return {"util_interval_tokens": [lo, hi], "fits_at_preemption": sorted(fits),
            "max_concurrent": {c: max_concurrent(spec, c) for c in GB}, "passes": per,
            "supported": passing[0] if len(passing) == 1 else None}


def identify_reported_formula(rows: list[dict]) -> dict:
    """Test hypotheses for reported_tok_s against every row. Tolerance = the log's own rounding:
    +/-0.05 on the rate plus the effect of +/-0.005 s on wall_clock_s."""
    hyps = {"prompt_plus_gen": lambda r: (r["prompt_len"] + r["gen_len"]) * r["num_requests"],
            "gen_only": lambda r: r["gen_len"] * r["num_requests"]}
    out = {}
    for name, tokens in hyps.items():
        match = 0
        for r in rows:
            pred = tokens(r) / r["wall_clock_s"]
            tol = 0.05 + pred * 0.005 / r["wall_clock_s"]
            match += abs(pred - r["reported_tok_s"]) <= tol
        out[name] = {"rows_matching": match, "rows": len(rows)}
    return out


def timing_inconsistency(rows: list[dict]) -> list[dict]:
    return [{"batch_size": r["batch_size"], "prompt_len": r["prompt_len"], "wall_s": r["wall_clock_s"],
             "e2e_p95_s": r["e2e_ms_p95"] / 1000, "e2e_p95_exceeds_wall": r["e2e_ms_p95"] / 1000 > r["wall_clock_s"]}
            for r in rows]


def fit_from_preemption(rows: list[dict]) -> list[dict]:
    """At rows with preemption, the sequences that could stay resident = batch - preempted."""
    return [{"batch_size": r["batch_size"], "preempted_seqs": r["preempted_seqs"],
             "fit": r["batch_size"] - r["preempted_seqs"]} for r in rows if r["preempted_seqs"]]
