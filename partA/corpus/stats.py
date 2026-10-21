#!/usr/bin/env python3
"""Descriptive statistics for the A1 corpus; writes partA/corpus/stats.json.

    python partA/corpus/stats.py

Every number in partA/corpus/README.md comes from this script's output.
Ratios are ratio-of-totals (sum over sum) vs the parallel English text.
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from units import cluster_bootstrap_ratio, count_bytes, count_codepoints, count_graphemes, count_words  # noqa: E402

PREPARED = HERE / "prepared"
TOY = HERE.parents[1] / "starter_kit" / "corpus_sample"
LANGS = ["eng_Latn", "hin_Deva", "kan_Knda", "tam_Taml"]
SPLITS = ["dev", "devtest"]
UNITS = {"words": count_words, "codepoints": count_codepoints, "graphemes": count_graphemes, "bytes": count_bytes}
LATIN = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")


def read_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return text.split("\n")[:-1] if text.endswith("\n") else text.split("\n")


def read_metadata(split: str) -> list[dict]:
    rows = read_lines(PREPARED / f"metadata_{split}.tsv")
    header = rows[0].split("\t")
    return [dict(zip(header, r.split("\t"))) for r in rows[1:]]


def compute_stats() -> dict:
    meta = {s: read_metadata(s) for s in SPLITS}
    text = {lang: {s: read_lines(PREPARED / f"{lang}.{s}.txt") for s in SPLITS} for lang in LANGS}
    # article id = URL, prefixed by split so dev/devtest articles stay distinct
    articles = [f"{s}:{m['URL']}" for s in SPLITS for m in meta[s]]

    out = {
        "sentences": {s: len(meta[s]) for s in SPLITS},
        "articles": {s: len({m["URL"] for m in meta[s]}) for s in SPLITS},
        "domains": {s: dict(collections.Counter(m["domain"] for m in meta[s])) for s in SPLITS},
        "top_topics": collections.Counter(
            # metadata mixes "Travel"/"travel"; case-fold so counts aren't split
            t.strip().lower() for s in SPLITS for m in meta[s] for t in m["topic"].split(",") if t.strip()
        ).most_common(10),
        "languages": {},
        "ratio_vs_eng": {},
        "ratio_vs_eng_by_split": {},
        "bootstrap_codepoint_ratio": {},
    }

    per_line = {}  # lang -> unit -> list over all 2009 lines
    for lang in LANGS:
        lines = text[lang]["dev"] + text[lang]["devtest"]
        per_line[lang] = {u: [f(x) for x in lines] for u, f in UNITS.items()}
        latin_chars = sum(sum(c in LATIN for c in x) for x in lines)
        out["languages"][lang] = {
            "sentences": len(lines),
            **{u: sum(v) for u, v in per_line[lang].items()},
            "mean_words_per_sentence": round(sum(per_line[lang]["words"]) / len(lines), 2),
            "duplicate_lines": len(lines) - len(set(lines)),
            "lines_with_latin_letters": sum(any(c in LATIN for c in x) for x in lines),
            "latin_letter_share_of_codepoints": round(latin_chars / sum(per_line[lang]["codepoints"]), 4),
        }

    eng = per_line["eng_Latn"]
    for lang in LANGS:
        out["ratio_vs_eng"][lang] = {
            u: [round(v, 4) for v in cluster_bootstrap_ratio(per_line[lang][u], eng[u], articles, seed=0)]
            for u in UNITS
        }
        n_dev = out["sentences"]["dev"]
        out["ratio_vs_eng_by_split"][lang] = {
            s: round(sum(per_line[lang]["codepoints"][sl]) / sum(eng["codepoints"][sl]), 4)
            for s, sl in {"dev": slice(0, n_dev), "devtest": slice(n_dev, None)}.items()
        }
        cp, ecp = per_line[lang]["codepoints"], eng["codepoints"]
        out["bootstrap_codepoint_ratio"][lang] = {
            "article_clustered": [round(v, 4) for v in cluster_bootstrap_ratio(cp, ecp, articles, seed=0)],
            "iid": [round(v, 4) for v in cluster_bootstrap_ratio(cp, ecp, list(range(len(cp))), seed=0)],
        }

    toy = {}
    for name in ("eng", "hin"):
        lines = [x.strip() for x in read_lines(TOY / f"{name}_sample.txt") if x.strip()]
        toy[name] = {
            "sentences": len(lines),
            "mean_words_per_sentence": round(sum(map(count_words, lines)) / len(lines), 2),
            "mean_codepoints_per_sentence": round(sum(map(len, lines)) / len(lines), 2),
        }
    out["toy_corpus_for_comparison"] = toy
    for lang in ("eng_Latn", "hin_Deva"):
        out["languages"][lang]["mean_codepoints_per_sentence"] = round(
            out["languages"][lang]["codepoints"] / out["languages"][lang]["sentences"], 2
        )
    return out


def main() -> None:
    stats = compute_stats()
    # newline="\n": without it Windows writes \r\n and the bytes differ per OS
    (HERE / "stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
