#!/usr/bin/env python3
"""A4 evidence: how well each tokenizer's vocabulary covers each language.

    python partA/analysis/coverage.py      # writes partA/analysis/coverage.json

Per language x tokenizer, on the FLORES text prepared as V1 (NFC, no lowercasing):
- code points (and relative to English): how much text there is for the same content;
- tokens per code point: how efficiently the vocabulary encodes the script;
- fragment share: tokens that do not decode to whole characters, i.e. byte-level fallback.

It explains why kan/tam cost more (A3), and it is the baseline for A4's production metric.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import fertility_v1 as v1  # noqa: E402

OUT = HERE / "coverage.json"
REPLACEMENT = "�"  # what a partial UTF-8 sequence decodes to


def coverage_row(raw_lines, encode, decode, cfg=v1.V1) -> dict:
    texts = [v1.measured_text(line, cfg) for line in v1.prepare(raw_lines, cfg)]
    ids = [i for t in texts for i in encode(t)]
    partial = {i: REPLACEMENT in decode([i]) for i in set(ids)}  # decode each distinct id once
    cps = sum(len(t) for t in texts)
    return {"codepoints": cps, "tokens": len(ids), "tokens_per_codepoint": len(ids) / cps,
            "fragment_share": sum(partial[i] for i in ids) / len(ids)}


def relative_to_english(rows: dict) -> dict:
    return {lang: r["codepoints"] / rows["eng"]["codepoints"] for lang, r in rows.items()}


def load_codec(spec: str):
    """(encode, decode) for a pinned tokenizer spec; never adds special tokens."""
    kind, name, revision = v1.parse_tokenizer_spec(spec)
    if kind == "hf":
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(name, revision=revision)
        return (lambda s: tok.encode(s, add_special_tokens=False),
                lambda ids: tok.decode(ids, clean_up_tokenization_spaces=False))
    import tiktoken

    enc = tiktoken.get_encoding(name)
    return enc.encode, enc.decode


def build() -> dict:
    from analysis.premium import TOKENIZERS
    from audit.experiments import load_corpora

    corpora = load_corpora()["flores"]
    out = {"by_tokenizer": {}}
    for label, spec in TOKENIZERS.items():
        encode, decode = load_codec(spec)
        rows = {lang: coverage_row(lines, encode, decode) for lang, lines in corpora.items()}
        rel = relative_to_english(rows)
        for lang in rows:
            rows[lang]["codepoints_vs_eng"] = rel[lang]
        out["by_tokenizer"][label] = {"spec": spec, "by_lang": rows}
    return out


def main() -> None:
    res = build()
    OUT.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(HERE.parents[1])}")
    for label, t in res["by_tokenizer"].items():
        print(f"== {label}")
        for lang, r in t["by_lang"].items():
            print(f"  {lang}: code points vs eng {r['codepoints_vs_eng']:.2f}  tokens/code point "
                  f"{r['tokens_per_codepoint']:.3f}  fragment share {r['fragment_share']:.1%}")


if __name__ == "__main__":
    main()
