#!/usr/bin/env python3
"""Render partA/A2_results.md from the committed JSON evidence (never hand-typed).

    python partA/audit/report.py

Sections follow the user-agreed order: each fix alone (vs v0), then the
ablation (leave-one-out from V1), then the cumulative path, then the
instrument (F9). A staleness test keeps the committed file equal to render().
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESULTS = HERE / "results"
OUT = ROOT / "partA" / "A2_results.md"
LANGS = ("eng", "hin", "kan", "tam")
FINDING_ORDER = ["F1", "F3", "F4", "F2", "F6", "F7", "F8_graphemes", "F8_bytes"]  # chronological


def tok_name(spec: str) -> str:
    return spec.split("@")[0].split("/")[-1].removeprefix("hf:")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def isolated_section() -> list[str]:
    out = ["## 1. Each fix alone (v0 vs v0 + that one fix)", "",
           "Delta % = (variant − v0) / v0. Verdict per D-14: *negligible* if |Δ| < 1% on every metric. "
           "Lines changed = tokens / words / any metric.", ""]
    for name in FINDING_ORDER:
        files = sorted(RESULTS.glob(f"{name}_*.json"))
        if not files:
            continue
        variant = load(files[0])["variant"]
        out += [f"### {name}: `{json.dumps(variant)}`", "",
                "| tokenizer | corpus | lang | metric (v0 → fix) | Δ | ratio vs eng (v0 → fix) | Δ | lines changed | verdict |",
                "|---|---|---|---|---|---|---|---|---|"]
        for f in files:
            r = load(f)
            for corpus in ("toy", "flores"):
                for lang in LANGS:
                    if lang not in r["before"][corpus]:
                        continue
                    b, a, d = (r[k][corpus][lang] for k in ("before", "after", "delta_pct"))
                    lc = r["lines_changed"][corpus][lang]
                    out.append(
                        f"| {tok_name(r['tokenizer'])} | {corpus} | {lang} | {b['fertility']:.4f} → {a['fertility']:.4f} "
                        f"| {d['fertility']:+.2f}% | {b['fertility_ratio_vs_eng']:.3f} → {a['fertility_ratio_vs_eng']:.3f} "
                        f"| {d['fertility_ratio_vs_eng']:+.2f}% | {lc['tokens']}/{lc['words']}/{lc['any_metric']} "
                        f"| {r['threshold_verdict'][corpus]['by_language'][lang]} |")
        if name.startswith("F8"):
            out += ["", "tok/char ratio vs eng (the metric F8 changes):", "",
                    "| tokenizer | corpus | lang | code points (v0) | this unit | Δ |", "|---|---|---|---|---|---|"]
            for f in files:
                r = load(f)
                for corpus in ("toy", "flores"):
                    for lang in LANGS[1:]:
                        if lang not in r["before"][corpus]:
                            continue
                        b, a = r["before"][corpus][lang], r["after"][corpus][lang]
                        out.append(f"| {tok_name(r['tokenizer'])} | {corpus} | {lang} | {b['tok_per_char_ratio_vs_eng']:.3f} "
                                   f"| {a['tok_per_char_ratio_vs_eng']:.3f} "
                                   f"| {r['delta_pct'][corpus][lang]['tok_per_char_ratio_vs_eng']:+.2f}% |")
        out.append("")
    return out


def ablation_sections() -> list[str]:
    ab = load(HERE / "ablation.json")
    fixes = list(ab["fixes"])
    out = ["## 2. Ablation: leave-one-out from fully corrected V1", "",
           f"V1 = v0 with fixes {', '.join(fixes)} (F4 and F6 are 'fine as written', so V1 keeps v0's behaviour). "
           "Each column switches one fix back to v0. Contribution = (V1 − V1 without fix) / (V1 without fix). "
           "Metric: tokens per parallel sentence, ratio vs eng, FLORES.", ""]
    for tok, r in ab["by_tokenizer"].items():
        out += [f"### {tok_name(tok)}", "",
                "| lang | V1 | " + " | ".join(f"without {k} (contribution)" for k in fixes) + " |",
                "|---|---|" + "---|" * len(fixes)]
        for lang in LANGS[1:]:
            cells = []
            for k in fixes:
                m = r["leave_one_out"][k]
                cells.append(f"{m['metrics']['flores'][lang]['fertility_ratio_vs_eng']:.3f} "
                             f"({m['delta_pct_v1_vs_without']['flores'][lang]['fertility_ratio_vs_eng']:+.2f}%)")
            out.append(f"| {lang} | {r['v1']['flores'][lang]['fertility_ratio_vs_eng']:.3f} | " + " | ".join(cells) + " |")
        out.append("")
    out += ["## 3. Cumulative path v0 → V1", "",
            "One fix added per step, in the pre-registered order. Ratio vs eng, FLORES. Note the unit changes at +F7 "
            "(tokens per word → tokens per parallel sentence).", ""]
    for tok, r in ab["by_tokenizer"].items():
        steps = [s["step"] for s in r["cumulative"]]
        out += [f"### {tok_name(tok)}", "", "| lang | " + " | ".join(steps) + " |", "|---|" + "---|" * len(steps)]
        for lang in LANGS[1:]:
            out.append(f"| {lang} | " + " | ".join(
                f"{s['metrics']['flores'][lang]['fertility_ratio_vs_eng']:.3f}" for s in r["cumulative"]) + " |")
        out.append("")
    return out


def instrument_section() -> list[str]:
    out = ["## 4. The instrument (F9): gpt2 → Llama-3.2-3B proxy for FLM-4B", "",
           "Config held fixed, tokenizer swapped. Proxy caveat: architecture numbers match model_spec.md, "
           "parameter count does not (D-04).", "",
           "| config | corpus | lang | ratio vs eng, gpt2 | Llama-3.2-3B | Δ |", "|---|---|---|---|---|---|"]
    for f in sorted(RESULTS.glob("F9_*.json")):
        r = load(f)
        for corpus in ("toy", "flores"):
            for lang in LANGS[1:]:
                if lang not in r["a"][corpus]:
                    continue
                out.append(f"| {r['config']} | {corpus} | {lang} | {r['a'][corpus][lang]['fertility_ratio_vs_eng']:.3f} "
                           f"| {r['b'][corpus][lang]['fertility_ratio_vs_eng']:.3f} "
                           f"| {r['delta_pct'][corpus][lang]['fertility_ratio_vs_eng']:+.2f}% |")
    return out + [""]


def render() -> str:
    head = ["# A2 results (generated)", "",
            "_Generated by `python partA/audit/report.py` from `partA/audit/results/*.json` and "
            "`partA/audit/ablation.json`. Do not edit by hand; a test fails if this file is stale._", "",
            "Configs: **v0** = the original script (reproduced exactly); **V1** = fully corrected "
            "(`partA/fertility_v1.py`). Corpora: toy = `starter_kit/corpus_sample`; FLORES = A1 corpus "
            "(2,009 parallel sentences per language). Interpretation is in `partA/A2_audit.md`.", ""]
    return "\n".join(head + isolated_section() + ablation_sections() + instrument_section())


def main() -> None:
    OUT.write_text(render(), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(render().splitlines())} lines)")


if __name__ == "__main__":
    main()
