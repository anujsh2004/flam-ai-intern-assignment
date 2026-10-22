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


def load_bench(path: Path = BENCH) -> list[dict]:
    """Typed rows of the load-test log. The original file is CRLF; csv handles it with newline=''."""
    with open(path, encoding="utf-8", newline="") as f:
        return [{k: int(v) if k in INT_COLS else float(v) for k, v in row.items()} for row in csv.DictReader(f)]
