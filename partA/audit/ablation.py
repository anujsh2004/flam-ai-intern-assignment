#!/usr/bin/env python3
"""A2 ablation (user-specified order): leave-one-out from the fully corrected V1
first, then the cumulative path from v0. Writes partA/audit/ablation.json.

    python partA/audit/ablation.py

Only fixes where V1 differs from v0 are ablated; F4 (NFC) and F6 (special
tokens) are "looks suspicious but fine", so V1 keeps v0's behaviour for them.
"""
import json
import sys
from dataclasses import fields
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import fertility_v1 as v1  # noqa: E402
from audit.experiments import LLAMA, XLMR, load_corpora, measure  # noqa: E402

OUT = HERE / "ablation.json"
TOKENIZERS = ["gpt2", XLMR, LLAMA]
# finding -> Config field; order = cumulative path order (pre-registered in plan.md)
FIX_FIELD = {"F1": "split", "F3": "lowercase", "F2": "aggregate", "F7": "denominator"}
V1_FIXES = {k: f for k, f in FIX_FIELD.items() if getattr(v1.V1, f) != getattr(v1.V0, f)}
assert {f.name for f in fields(v1.Config) if getattr(v1.V1, f.name) != getattr(v1.V0, f.name)} == set(V1_FIXES.values())


def leave_one_out_configs() -> dict:
    return {k: v1.replace(v1.V1, **{f: getattr(v1.V0, f)}) for k, f in V1_FIXES.items()}


def cumulative_configs() -> list[tuple[str, v1.Config]]:
    steps, cfg = [("v0", v1.V0)], v1.V0
    for k, f in V1_FIXES.items():
        cfg = v1.replace(cfg, **{f: getattr(v1.V1, f)})
        steps.append((f"+{k}", cfg))
    return steps


def pct(new: dict, old: dict) -> dict:
    return {c: {l: {m: (new[c][l][m] - v) / v * 100 for m, v in ms.items()} for l, ms in ls.items()}
            for c, ls in old.items()}


def run_ablation(encode, corpora) -> dict:
    full = measure(v1.V1, encode, corpora)
    loo = {}
    for k, cfg in leave_one_out_configs().items():
        m = measure(cfg, encode, corpora)
        loo[k] = {"metrics": m, "delta_pct_v1_vs_without": pct(full, m)}
    cum, prev = [], None
    for step, cfg in cumulative_configs():
        m = measure(cfg, encode, corpora)
        cum.append({"step": step, "metrics": m, "delta_pct_vs_previous": pct(m, prev) if prev else None})
        prev = m
    return {"v1": full, "leave_one_out": loo, "cumulative": cum}


def build() -> dict:
    corpora = load_corpora()
    return {"fixes": V1_FIXES, "by_tokenizer": {t: run_ablation(v1.load_tokenizer(t), corpora) for t in TOKENIZERS}}


def main() -> None:
    res = build()
    OUT.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(HERE.parents[1])}")
    for tok, r in res["by_tokenizer"].items():
        print(f"== {tok.split('@')[0]}  (FLORES ratio vs eng)")
        for lang in ("hin", "kan", "tam"):
            loo = ", ".join(f"-{k}: {r['leave_one_out'][k]['metrics']['flores'][lang]['fertility_ratio_vs_eng']:.3f}"
                            for k in V1_FIXES)
            path = " -> ".join(f"{s['metrics']['flores'][lang]['fertility_ratio_vs_eng']:.3f}" for s in r["cumulative"])
            print(f"  {lang}: V1 {r['v1']['flores'][lang]['fertility_ratio_vs_eng']:.3f} | without {loo}")
            print(f"       cumulative v0 -> V1: {path}")


if __name__ == "__main__":
    main()
