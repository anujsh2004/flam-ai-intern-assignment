#!/usr/bin/env python3
"""Part C back-of-envelope arithmetic. Every input is a named, labelled assumption;
every number quoted in partC/memo.md is generated here (python partC/arithmetic.py).

Token premiums are read from A3 (partA/analysis/results.json), not retyped.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "results.json"
A3 = ROOT / "partA" / "analysis" / "results.json"

ASSUMPTIONS = {
    # constraints from the brief
    "reviewer_hours_per_week": 10, "gpu_weeks": 2, "weeks_to_launch_review": 3,
    "launch_langs": ["hin", "kan"],  # user decision: reviewer covers hi + kn
    # planning assumptions (labelled in the memo)
    "reviewer_rates_per_h": [30, 60, 90], "planning_rate_per_h": 60,
    "calibration_judgements": 50, "screen_variants": 2, "screen_n_per_lang": 100, "final_n_per_lang": 200,
    "synthetic_spot_check": 200,
    "pairs_per_lang": 2000, "eng_tokens_per_pair": 200, "epochs": 3,  # SFT fallback (LoRA)
    "params": 4.2e9, "a100_bf16_flops": 312e12, "mfu": 0.40, "train_flops_per_param_token": 6,
    "rewriter_params": 1.0e9,
}


def premiums() -> dict:
    """Serving-tokenizer (Llama-3.2-3B proxy) tokens-per-sentence premium vs English, from A3."""
    r = json.loads(A3.read_text(encoding="utf-8"))["by_tokenizer"]["llama"]["premium"]
    return {lang: r[lang]["sentence"][0] for lang in ("hin", "kan", "tam")}


def reviewer_capacity(a: dict) -> dict:
    h_gpu = a["reviewer_hours_per_week"] * a["gpu_weeks"]
    return {"hours_in_gpu_window": h_gpu, "hours_to_launch_review": a["reviewer_hours_per_week"] * a["weeks_to_launch_review"],
            "judgements_by_rate": {r: h_gpu * r for r in a["reviewer_rates_per_h"]}}


def budget_plan(a: dict, rate: int) -> dict:
    per_week = a["reviewer_hours_per_week"] * rate
    n_lang = len(a["launch_langs"])
    screening = a["screen_variants"] * n_lang * a["screen_n_per_lang"]
    w1 = {"available": per_week, "calibration": a["calibration_judgements"], "screening": screening}
    w1["spare"] = per_week - w1["calibration"] - screening
    final = n_lang * a["final_n_per_lang"]
    w2 = {"available": per_week, "final_eval": final, "synthetic_spot_check": a["synthetic_spot_check"]}
    w2["spare"] = per_week - final - w2["synthetic_spot_check"]
    return {"rate": rate, "week1": w1, "week2": w2, "fits": w1["spare"] >= 0 and w2["spare"] >= 0}


def ci_half_width(p: float, n: int) -> float:
    """Normal-approximation 95% CI half-width for a proportion."""
    return 1.96 * math.sqrt(p * (1 - p) / n)


def sft_volume(a: dict) -> dict:
    prem = premiums()
    per_pair = {lang: a["eng_tokens_per_pair"] * prem[lang] for lang in a["launch_langs"]}
    per_epoch = sum(a["pairs_per_lang"] * t for t in per_pair.values())
    return {"tokens_per_pair": per_pair, "tokens_per_epoch": per_epoch, "tokens_total": per_epoch * a["epochs"]}


def training_time(a: dict, tokens: float) -> dict:
    tps = a["a100_bf16_flops"] * a["mfu"] / (a["train_flops_per_param_token"] * a["params"])
    return {"tokens_per_s": tps, "hours": tokens / tps / 3600}


def finetune_memory_gb(a: dict) -> dict:
    # full FT: bf16 weights (2) + bf16 grads (2) + fp32 Adam m,v (8) + fp32 master (4) bytes/param
    return {"full_ft_states_gb": a["params"] * 16 / 1e9, "lora_base_weights_gb": a["params"] * 2 / 1e9,
            "a100_gb": 80}


def rewriter_overhead(a: dict) -> dict:
    """Decode is memory-bound: per-token cost ~ parameter bytes read. A rewriter that re-generates
    the whole reply adds rewriter/main of the main model's decode work, on every request."""
    extra = a["rewriter_params"] / a["params"]
    return {"extra_decode_fraction": extra, "capacity_loss_fraction": 1 - 1 / (1 + extra)}


def build() -> dict:
    a = ASSUMPTIONS
    vol = sft_volume(a)
    return {"assumptions": a, "premiums": premiums(), "reviewer": reviewer_capacity(a),
            "budget": {str(r): budget_plan(a, r) for r in a["reviewer_rates_per_h"]},
            "ci": {"casual_0.70_n200": ci_half_width(0.70, 200), "meaning_0.95_n200": ci_half_width(0.95, 200),
                   "screen_0.50_n100": ci_half_width(0.50, 100)},
            "sft": vol, "training": training_time(a, vol["tokens_total"]), "memory": finetune_memory_gb(a),
            "rewriter": rewriter_overhead(a)}


def main() -> None:
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
