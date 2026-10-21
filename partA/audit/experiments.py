#!/usr/bin/env python3
"""Measure one audited fix in isolation: v0 vs (v0 + that fix).

    python partA/audit/experiments.py F1 [--tokenizer gpt2]

Writes partA/audit/results/<finding>_<tokenizer>.json. Effect size and the
negligible/material line follow D-14 (|delta| < 1% on every reported metric).
"""
import argparse
import json
import sys
from dataclasses import fields
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import fertility_v1 as v1  # noqa: E402

ROOT = HERE.parents[1]
TOY = ROOT / "starter_kit" / "corpus_sample"
FLORES = ROOT / "partA" / "corpus" / "prepared"
FLORES_LANGS = {"eng": "eng_Latn", "hin": "hin_Deva", "kan": "kan_Knda", "tam": "tam_Taml"}
THRESHOLD_PCT = 1.0  # D-14, pre-registered
# pinned revisions so results are reproducible (D-04)
XLMR = "hf:FacebookAI/xlm-roberta-base@e73636d4f797dec63c3081bb6ed5c7b0bb3f2089"

# finding -> config that differs from v0 in exactly that one fix
FINDINGS = {
    "F1": v1.replace(v1.V0, split="whitespace"),
    "F3": v1.replace(v1.V0, lowercase=False),
    "F4": v1.replace(v1.V0, nfc=False),
    "F2": v1.replace(v1.V0, aggregate="total"),
}


def load_corpora() -> dict:
    toy = {lang: v1.read_raw_lines(TOY / f"{lang}_sample.txt") for lang in ("eng", "hin")}
    flores = {
        lang: v1.read_raw_lines(FLORES / f"{code}.dev.txt") + v1.read_raw_lines(FLORES / f"{code}.devtest.txt")
        for lang, code in FLORES_LANGS.items()
    }
    return {"toy": toy, "flores": flores}


def measure(cfg, encode, corpora) -> dict:
    out = {}
    for corpus, langs in corpora.items():
        res = {lang: v1.analyze(v1.prepare(lines, cfg), encode, cfg) for lang, lines in langs.items()}
        for r in res.values():
            r["fertility_ratio_vs_eng"] = r["fertility"] / res["eng"]["fertility"]
            r["tok_per_char_ratio_vs_eng"] = r["tok_per_char"] / res["eng"]["tok_per_char"]
        out[corpus] = res
    return out


def lines_changed(before_cfg, after_cfg, encode, lines) -> dict:
    """Per-line changes, kept apart: token count, word count, and any reported metric
    (the last also catches tok/char moving only because len(line) changed)."""
    out = {"tokens": 0, "words": 0, "any_metric": 0}
    for x, y in zip(v1.prepare(lines, before_cfg), v1.prepare(lines, after_cfg)):
        mx, my = v1.measured_text(x, before_cfg), v1.measured_text(y, after_cfg)
        out["tokens"] += len(encode(mx)) != len(encode(my))
        out["words"] += v1.count_words(mx, before_cfg) != v1.count_words(my, after_cfg)
        out["any_metric"] += v1.analyze([x], encode, before_cfg) != v1.analyze([y], encode, after_cfg)
    return out


def threshold_verdict(deltas: dict) -> str:
    return "negligible" if all(abs(d) < THRESHOLD_PCT for d in deltas.values()) else "material"


def compare(before_cfg, after_cfg, encode, corpora) -> dict:
    before = measure(before_cfg, encode, corpora)
    after = measure(after_cfg, encode, corpora)
    delta = {
        corpus: {
            lang: {k: (after[corpus][lang][k] - v) / v * 100 for k, v in metrics.items()}
            for lang, metrics in langs.items()
        }
        for corpus, langs in before.items()
    }
    changed = {
        corpus: {lang: lines_changed(before_cfg, after_cfg, encode, lines) for lang, lines in langs.items()}
        for corpus, langs in corpora.items()
    }
    own = ("fertility", "tok_per_char")  # a language's own metrics, excluding ratios vs eng
    verdict = {
        corpus: {
            "overall": threshold_verdict({f"{lang}.{k}": d for lang, m in langs.items() for k, d in m.items()}),
            "by_language": {lang: threshold_verdict(m) for lang, m in langs.items()},
            "by_language_own_metrics": {lang: threshold_verdict({k: m[k] for k in own}) for lang, m in langs.items()},
        }
        for corpus, langs in delta.items()
    }
    return {"before": before, "after": after, "delta_pct": delta, "lines_changed": changed, "threshold_verdict": verdict}


def changed_fields(cfg, base=v1.V0) -> dict:
    return {f.name: getattr(cfg, f.name) for f in fields(cfg) if getattr(cfg, f.name) != getattr(base, f.name)}


def result_record(finding: str, tokenizer: str, cfg, res: dict) -> dict:
    """The exact JSON record committed under results/ (rebuilt by the staleness test).
    The variant is stored as its difference from v0, so new Config fields don't churn old records."""
    return {"finding": finding, "tokenizer": tokenizer, "variant": changed_fields(cfg), **res}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("finding", choices=sorted(FINDINGS))
    ap.add_argument("--tokenizer", default="gpt2")
    args = ap.parse_args()

    cfg = FINDINGS[args.finding]
    res = result_record(args.finding, args.tokenizer, cfg,
                        compare(v1.V0, cfg, v1.load_tokenizer(args.tokenizer), load_corpora()))
    out = HERE / "results" / f"{args.finding}_{args.tokenizer.replace('/', '_').replace(':', '_')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"{args.finding} ({args.tokenizer}): {res['variant']}  -> {out.relative_to(ROOT)}")
    for corpus, langs in res["delta_pct"].items():
        print(f"[{corpus}] verdict: {res['threshold_verdict'][corpus]['overall']}")
        for lang, m in langs.items():
            print(f"  {lang}: {res['threshold_verdict'][corpus]['by_language'][lang]} "
                  f"(own metrics: {res['threshold_verdict'][corpus]['by_language_own_metrics'][lang]})")
            b, a = res["before"][corpus][lang], res["after"][corpus][lang]
            print(f"  {lang}: fertility {b['fertility']:.4f} -> {a['fertility']:.4f} ({m['fertility']:+.2f}%), "
                  f"ratio {b['fertility_ratio_vs_eng']:.4f} -> {a['fertility_ratio_vs_eng']:.4f} "
                  f"({m['fertility_ratio_vs_eng']:+.2f}%), lines changed {res['lines_changed'][corpus][lang]}")
    # note: 'any_metric' includes tok/char moving only via len(line); 'tokens' is the token-count effect


if __name__ == "__main__":
    main()
