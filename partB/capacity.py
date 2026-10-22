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


def goodput(r: dict) -> float:
    """Useful throughput: generated tokens of completed requests per second of the run."""
    return r["gen_len"] * r["num_requests"] / r["wall_clock_s"]


def goodput_two_ways(r: dict) -> dict:
    """(1) from wall_clock_s; (2) from the separately logged reported_tok_s, keeping only the
    generated share of the tokens it counts (formula identified on every row above)."""
    return {"from_wall_clock": goodput(r),
            "from_reported_column": r["reported_tok_s"] * r["gen_len"] / (r["prompt_len"] + r["gen_len"])}


def goodput_bounds(r: dict) -> dict:
    """Latency-column estimates. They use medians/p95 on a different clock than wall_clock_s
    (see timing_inconsistency), so they bracket the goodput rather than measure it."""
    per_request_p50_s = (r["ttft_ms_p50"] + (r["gen_len"] - 1) * r["itl_ms_p50"]) / 1000
    n_tokens = r["gen_len"] * r["num_requests"]
    return {"from_p50_ttft_itl": n_tokens / per_request_p50_s, "from_e2e_p95": n_tokens / (r["e2e_ms_p95"] / 1000)}


LONG = 3584


def long_sweep(rows: list[dict]) -> list[dict]:
    return sorted((r for r in rows if r["prompt_len"] == LONG), key=lambda r: r["batch_size"])


def anomaly(rows: list[dict]) -> dict:
    """Naive expectation: goodput rises with batch. Find where it stops and what changes there."""
    sweep = [{**r, "goodput": goodput(r)} for r in long_sweep(rows)]
    peak = max(sweep, key=lambda s: s["goodput"])
    i = sweep.index(peak)
    return {"peak_batch": peak["batch_size"], "up_to_peak": sweep[: i + 1], "after_peak": sweep[i + 1:]}


def option_a_cap(rows: list[dict], requests: int, cap: int) -> dict:
    """Cap concurrent sequences at a batch the log shows runs without preemption; the burst
    runs as ceil(requests / cap) waves of that logged run (no extrapolation)."""
    base = next(r for r in long_sweep(rows) if r["batch_size"] == cap)
    assert base["preempted_seqs"] == 0
    waves = -(-requests // cap)
    wall = waves * base["wall_clock_s"]
    observed = next(r for r in long_sweep(rows) if r["batch_size"] == requests)
    g = base["gen_len"] * requests / wall
    return {"cap": cap, "waves": waves, "wall_s": wall, "goodput": g, "observed_goodput": goodput(observed),
            "vs_observed_pct": (g / goodput(observed) - 1) * 100, "basis": f"logged b{cap} row x {waves}"}


def option_b_fp8(rows: list[dict], spec: dict, requests: int) -> dict:
    """fp8 KV halves bytes/element. If the batch then fits, extrapolate wall clock from a
    least-squares line through the non-preempting long rows. Quality impact: not measured."""
    fp8 = {**spec, "bytes_per_elem": 1}
    weights = spec["params"] * spec["bytes_per_elem"]  # weights stay fp16
    budget = spec["gpu_gb"] * GB["decimal"] * spec["gpu_memory_utilization"] - weights - spec["overhead_gb"] * GB["decimal"]
    cap = budget / seq_bytes(fp8)
    pts = [(r["batch_size"], r["wall_clock_s"]) for r in long_sweep(rows) if r["preempted_seqs"] == 0]
    mx = sum(x for x, _ in pts) / len(pts)
    my = sum(y for _, y in pts) / len(pts)
    slope = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)
    wall = my + slope * (requests - mx)
    observed = next(r for r in long_sweep(rows) if r["batch_size"] == requests)
    g = observed["gen_len"] * requests / wall
    return {"kv_bytes_per_token": kv_bytes_per_token(fp8), "max_concurrent": cap, "fits": requests <= cap,
            "wall_s": wall, "goodput": g, "vs_observed_pct": (g / goodput(observed) - 1) * 100,
            "basis": f"extrapolated line through b{pts[0][0]}..b{pts[-1][0]} to b{requests}"}


def option_c_max_model_len(rows: list[dict], spec: dict, new_max: int) -> dict:
    """Paged attention allocates KV per token, so capacity in tokens does not depend on
    max_model_len; requests longer than the limit are rejected."""
    long_reqs = [r for r in long_sweep(rows) if r["batch_size"] == 48][0]
    too_long = long_reqs["prompt_len"] + long_reqs["gen_len"] > new_max
    return {"new_max_model_len": new_max, "capacity_tokens_unchanged": True,
            "long_requests_rejected": long_reqs["num_requests"] if too_long else 0,
            "goodput": 0 if too_long else goodput(long_reqs)}


# user decision 2026-10-23: propose (a) cap at 24 (largest logged non-preempting batch);
# (b) fp8 KV is the follow-up experiment (needs a quality evaluation)
CHOSEN_CHANGE = {"propose": "a", "cap": 24, "follow_up_experiment": "b"}


def b4_expectations(rows: list[dict], cap: int) -> dict:
    """The serving counter that confirms the B2 mechanism and its expected values."""
    return {"counter": "vllm:num_preemptions_total",
            "long_sweep": [{"batch_size": r["batch_size"], "expected_min": r["preempted_seqs"]} for r in long_sweep(rows)],
            # no preemption expected if the cap is within the sequences the log shows fitting (25)
            "after_cap_48_request_burst": 0 if cap <= min(f["fit"] for f in fit_from_preemption(rows)) else None}


def timing_inconsistency(rows: list[dict]) -> list[dict]:
    return [{"batch_size": r["batch_size"], "prompt_len": r["prompt_len"], "wall_s": r["wall_clock_s"],
             "e2e_p95_s": r["e2e_ms_p95"] / 1000, "e2e_p95_exceeds_wall": r["e2e_ms_p95"] / 1000 > r["wall_clock_s"]}
            for r in rows]


def fit_from_preemption(rows: list[dict]) -> list[dict]:
    """At rows with preemption, the sequences that could stay resident = batch - preempted."""
    return [{"batch_size": r["batch_size"], "preempted_seqs": r["preempted_seqs"],
             "fit": r["batch_size"] - r["preempted_seqs"]} for r in rows if r["preempted_seqs"]]
