#!/usr/bin/env python3
"""A3: tokenization premium vs English on the parallel FLORES corpus.

    python partA/analysis/premium.py      # writes partA/analysis/results.json

Premium for a unit U = (sum T_lang / sum U_lang) / (sum T_eng / sum U_eng), a
ratio of totals (A2/F2). For U = sentence this is sum T_lang / sum T_eng, the
same content in both languages (A2/F7). 95% CIs come from an article-clustered
bootstrap that mirrors units.cluster_bootstrap_ratio (cross-checked in tests).
Design pre-registered in docs/plan.md Phase 3 and D-18.
"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import fertility_v1 as v1  # noqa: E402
from audit.experiments import INDICBERT, LLAMA, XLMR, load_corpora  # noqa: E402

OUT = HERE / "results.json"
TOKENIZERS = {"gpt2": "gpt2", "llama": LLAMA, "xlmr": XLMR, "indicbert": INDICBERT}
UNITS = ("words", "codepoints", "graphemes", "bytes", "sentence")
LANGS = ("hin", "kan", "tam")
N_BOOT, SEED = 2000, 0  # pre-registered


def sentence_table(encode, raw_lines, cfg=v1.V1) -> list[dict]:
    """Per-sentence token and unit counts for the text exactly as measured under cfg."""
    rows = []
    for line in v1.prepare(raw_lines, cfg):
        text = v1.measured_text(line, cfg)
        rows.append({"tokens": v1.count_tokens(text, encode, cfg),
                     **{u: v1.count_units(text, u, cfg) for u in UNITS}})
    return rows


def _stat(t_l, u_l, t_e, u_e) -> float:
    return (t_l / u_l) / (t_e / u_e)


def premium(lang_rows, eng_rows, unit, overhead=0) -> float:
    """Ratio of totals; `overhead` tokens are added per sentence (one request per sentence)."""
    t_l = sum(r["tokens"] + overhead for r in lang_rows)
    t_e = sum(r["tokens"] + overhead for r in eng_rows)
    return _stat(t_l, sum(r[unit] for r in lang_rows), t_e, sum(r[unit] for r in eng_rows))


def bootstrap_premium(lang_rows, eng_rows, unit, clusters, n_boot=N_BOOT, seed=SEED, alpha=0.05, overhead=0):
    """(point, lo, hi). Resamples whole articles; RNG scheme identical to units.cluster_bootstrap_ratio."""
    groups = {}
    for lr, er, c in zip(lang_rows, eng_rows, clusters):
        g = groups.setdefault(c, [0.0, 0.0, 0.0, 0.0])
        g[0] += lr["tokens"] + overhead
        g[1] += lr[unit]
        g[2] += er["tokens"] + overhead
        g[3] += er[unit]
    sums = list(groups.values())

    def stat(sample):
        return _stat(*(sum(g[i] for g in sample) for i in range(4)))

    point = stat(sums)
    rng = random.Random(seed)
    stats = sorted(stat([sums[rng.randrange(len(sums))] for _ in sums]) for _ in range(n_boot))
    return point, stats[int(alpha / 2 * n_boot)], stats[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]


def _percentile(sorted_vals, q) -> float:
    pos = (len(sorted_vals) - 1) * q  # linear interpolation, numpy's default
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def spread(lang_rows, eng_rows) -> dict:
    """Distribution of per-sentence premiums T_lang,i / T_eng,i."""
    vals = sorted(lr["tokens"] / er["tokens"] for lr, er in zip(lang_rows, eng_rows))
    return {"median": _percentile(vals, 0.5), "p10": _percentile(vals, 0.1), "p90": _percentile(vals, 0.9)}


def article_ids() -> list[str]:
    """One article id per FLORES sentence (dev then devtest), as in A1's stats.py."""
    from corpus.stats import SPLITS, read_metadata

    return [f"{s}:{m['URL']}" for s in SPLITS for m in read_metadata(s)]


def build() -> dict:
    corpora, clusters = load_corpora()["flores"], article_ids()
    out = {"design": {"n_boot": N_BOOT, "seed": SEED, "alpha": 0.05, "units": list(UNITS),
                      "statistic": "ratio of totals vs eng", "cluster": "FLORES article URL"},
           "by_tokenizer": {}}
    for label, spec in TOKENIZERS.items():
        encode = v1.load_tokenizer(spec)
        table = {lang: sentence_table(encode, lines) for lang, lines in corpora.items()}
        res = {"spec": spec, "num_special_tokens": encode.num_special_tokens,
               "tokens_total": {lang: sum(r["tokens"] for r in rows) for lang, rows in table.items()},
               "premium": {}, "premium_with_overhead": {}, "spread": {}}
        for lang in LANGS:
            res["premium"][lang] = {u: list(bootstrap_premium(table[lang], table["eng"], u, clusters)) for u in UNITS}
            res["premium_with_overhead"][lang] = list(bootstrap_premium(
                table[lang], table["eng"], "sentence", clusters, overhead=encode.num_special_tokens))
            res["spread"][lang] = spread(table[lang], table["eng"])
        out["by_tokenizer"][label] = res
    return out


def main() -> None:
    res = build()
    OUT.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(HERE.parents[1])}")
    for label, r in res["by_tokenizer"].items():
        print(f"== {label} (specials/request {r['num_special_tokens']})")
        for lang in LANGS:
            p = r["premium"][lang]
            cells = "  ".join(f"{u}: {p[u][0]:.3f} [{p[u][1]:.3f}, {p[u][2]:.3f}]" for u in UNITS)
            s = r["spread"][lang]
            print(f"  {lang}: {cells}")
            print(f"       +overhead: {r['premium_with_overhead'][lang][0]:.3f} | per-sentence median "
                  f"{s['median']:.3f} p10 {s['p10']:.3f} p90 {s['p90']:.3f}")


if __name__ == "__main__":
    main()
