#!/usr/bin/env python3
"""fertility_v1.py -- audited version of starter_kit/fertility.py (A2).

Every behaviour the audit questions is an explicit Config field with a CLI
flag, so each fix can be switched on or off in isolation. `--v0` reproduces
the original script exactly (tested byte-for-byte).

Usage:
    python partA/fertility_v1.py --corpus eng=PATH --corpus hin=PATH \
                                 --tokenizer gpt2 [--v0]
"""
import argparse
import unicodedata
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    """Settings for one measurement; fields are added one audited fix at a time."""


V0 = Config()  # original fertility.py behaviour


def load_tokenizer(spec: str):
    if spec.startswith("hf:"):
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(spec[3:])
        return lambda s: tok.encode(s, add_special_tokens=False)
    import tiktoken

    return tiktoken.get_encoding(spec).encode


def read_lines(path: Path, cfg: Config) -> list[str]:
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            line = unicodedata.normalize("NFC", line)
            lines.append(line)
    return lines


def analyze(lines: list[str], encode, cfg: Config) -> dict:
    per_line_fertility = []
    per_line_tpc = []
    for line in lines:
        line = line.lower()
        tokens = encode(line)
        words = line.split(" ")
        per_line_fertility.append(len(tokens) / len(words))
        per_line_tpc.append(len(tokens) / len(line))
    n = len(per_line_fertility)
    return {"fertility": sum(per_line_fertility) / n, "tok_per_char": sum(per_line_tpc) / n}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", action="append", required=True, metavar="LANG=PATH")
    ap.add_argument("--tokenizer", default="gpt2")
    ap.add_argument("--v0", action="store_true", help="reproduce the original script exactly")
    args = ap.parse_args()
    cfg = V0

    encode = load_tokenizer(args.tokenizer)
    print(f"tokenizer: {args.tokenizer}")
    print(f"{'lang':<8}{'fertility (tok/word)':>22}{'tok/char':>12}")
    print("-" * 42)
    results = {}
    for spec in args.corpus:
        lang, path = spec.split("=", 1)
        r = analyze(read_lines(Path(path), cfg), encode, cfg)
        results[lang] = r
        print(f"{lang:<8}{r['fertility']:>22.2f}{r['tok_per_char']:>12.3f}")

    if len(results) >= 2:
        langs = list(results)
        base = langs[0]
        print()
        for lang in langs[1:]:
            ratio = results[lang]["fertility"] / results[base]["fertility"]
            print(f"{lang} is {ratio:.2f}x the fertility of {base} "
                  f"({'worse' if ratio > 1 else 'better'} tokenization)")


if __name__ == "__main__":
    main()
