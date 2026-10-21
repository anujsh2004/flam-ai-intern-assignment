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
from dataclasses import dataclass, replace
from pathlib import Path

from units import count_bytes, count_graphemes  # A1's tested unit counters (partA/units.py)


@dataclass(frozen=True)
class Config:
    """Settings for one measurement; fields are added one audited fix at a time."""

    # F1: "space" = line.split(" ") (v0; double spaces create empty words),
    #     "whitespace" = line.split() (only real words)
    split: str = "space"
    # F3: True = lowercase before tokenizing (v0). Served text is not lowercased,
    #     so this measures text the model never sees and changes eng but not Indic.
    lowercase: bool = True
    # F4: True = Unicode NFC before tokenizing (v0). Pre-registered as "looks
    #     suspicious but fine" (D-13); V1 keeps it. Effect is tokenizer-dependent.
    nfc: bool = True
    # F2: "line_mean" = mean of per-line ratios (v0; every line weighs the same,
    #     so the result depends on where line breaks fall); "total" = sum / sum
    aggregate: str = "line_mean"
    # F6: False = exclude tokenizer-added special tokens (v0: add_special_tokens=False).
    #     True counts them (e.g. XLM-R <s> </s>) on every line.
    special_tokens: bool = False
    # F7: unit the token count is divided by. "words" (v0) does not hold content
    #     constant across languages; "sentence" = tokens per parallel sentence does
    #     (provisional choice for V1; the single cost number is decided in A3, D-06).
    denominator: str = "words"
    # F8: unit for the tok/char column. "codepoints" (v0) means different things
    #     in different scripts; graphemes/bytes show how much the unit choice moves it.
    char_unit: str = "codepoints"


V0 = Config()  # original fertility.py behaviour
# fully corrected; the single source of CLI defaults
V1 = replace(V0, split="whitespace", lowercase=False, aggregate="total", denominator="sentence")
SPLITS = ("space", "whitespace")
AGGREGATES = ("line_mean", "total")
DENOMINATORS = ("words", "codepoints", "graphemes", "bytes", "sentence")
CHAR_UNITS = ("codepoints", "graphemes", "bytes")


def count_words(line: str, cfg: Config) -> int:
    if cfg.split == "space":
        return len(line.split(" "))
    if cfg.split == "whitespace":
        return len(line.split())
    raise ValueError(f"unknown split mode {cfg.split!r}")


def count_units(text: str, unit: str, cfg: Config) -> int:
    if unit == "words":
        return count_words(text, cfg)
    if unit == "codepoints":
        return len(text)
    if unit == "graphemes":
        return count_graphemes(text)
    if unit == "bytes":
        return count_bytes(text)
    if unit == "sentence":  # each line is one parallel sentence
        return 1
    raise ValueError(f"unknown unit {unit!r}")


def parse_tokenizer_spec(spec: str) -> tuple[str, str, str | None]:
    """'gpt2' -> tiktoken; 'hf:repo' or 'hf:repo@revision' -> HF (pin a revision for reproducibility)."""
    if spec.startswith("hf:"):
        repo, _, revision = spec[3:].partition("@")
        return "hf", repo, revision or None
    return "tiktoken", spec, None


def load_tokenizer(spec: str):
    """Return encode(s) -> token ids (never including special tokens), with
    encode.num_special_tokens = how many the tokenizer would add per sequence (F6)."""
    kind, name, revision = parse_tokenizer_spec(spec)
    if kind == "hf":
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(name, revision=revision)

        def encode(s):
            return tok.encode(s, add_special_tokens=False)

        encode.num_special_tokens = tok.num_special_tokens_to_add(pair=False)
        return encode
    import tiktoken

    enc = tiktoken.get_encoding(name)

    def encode(s):
        return enc.encode(s)

    encode.num_special_tokens = 0  # tiktoken's encode never adds special tokens
    return encode


def read_raw_lines(path: Path) -> list[str]:
    """Stripped, non-empty lines exactly as v0 reads them, before any normalisation."""
    with open(path, "r", encoding="utf-8") as f:
        return [line for line in (raw.strip() for raw in f) if line]


def prepare(lines: list[str], cfg: Config) -> list[str]:
    """Config-dependent text preparation applied before tokenizing."""
    if not cfg.nfc:
        return list(lines)
    return [unicodedata.normalize("NFC", line) for line in lines]


def read_lines(path: Path, cfg: Config) -> list[str]:
    return prepare(read_raw_lines(path), cfg)


def measured_text(line: str, cfg: Config) -> str:
    """The exact string that is tokenized and counted for one prepared line."""
    return line.lower() if cfg.lowercase else line


def count_tokens(text: str, encode, cfg: Config) -> int:
    specials = getattr(encode, "num_special_tokens", 0) if cfg.special_tokens else 0
    return len(encode(text)) + specials


def analyze(lines: list[str], encode, cfg: Config) -> dict:
    per_line_fertility = []
    per_line_tpc = []
    total_tokens = total_words = total_chars = 0
    for line in lines:
        line = measured_text(line, cfg)
        n_tokens = count_tokens(line, encode, cfg)
        n_words = count_units(line, cfg.denominator, cfg)  # "words" in v0
        n_chars = count_units(line, cfg.char_unit, cfg)  # code points in v0
        per_line_fertility.append(n_tokens / n_words)
        per_line_tpc.append(n_tokens / n_chars)
        total_tokens, total_words, total_chars = total_tokens + n_tokens, total_words + n_words, total_chars + n_chars
    if cfg.aggregate == "line_mean":
        n = len(per_line_fertility)
        return {"fertility": sum(per_line_fertility) / n, "tok_per_char": sum(per_line_tpc) / n}
    if cfg.aggregate == "total":
        return {"fertility": total_tokens / total_words, "tok_per_char": total_tokens / total_chars}
    raise ValueError(f"unknown aggregate mode {cfg.aggregate!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", action="append", required=True, metavar="LANG=PATH")
    ap.add_argument("--tokenizer", default="gpt2")
    ap.add_argument("--v0", action="store_true",
                    help="start from the original behaviour (default start: corrected V1); fix flags then override")
    # fix flags default to None = "keep the base value", so --v0 plus a flag isolates one fix
    ap.add_argument("--split", choices=SPLITS, default=None, help="F1: word splitting (V1: whitespace)")
    ap.add_argument("--lowercase", action=argparse.BooleanOptionalAction, default=None,
                    help="F3: lowercase before tokenizing (V1: --no-lowercase)")
    ap.add_argument("--nfc", action=argparse.BooleanOptionalAction, default=None,
                    help="F4: Unicode NFC before tokenizing (V1: --nfc)")
    ap.add_argument("--aggregate", choices=AGGREGATES, default=None,
                    help="F2: mean of per-line ratios or ratio of totals (V1: total)")
    ap.add_argument("--special-tokens", dest="special_tokens", action=argparse.BooleanOptionalAction, default=None,
                    help="F6: count tokenizer-added special tokens (V1: --no-special-tokens)")
    ap.add_argument("--denominator", choices=DENOMINATORS, default=None,
                    help="F7: unit the token count is divided by (V1: sentence)")
    ap.add_argument("--char-unit", dest="char_unit", choices=CHAR_UNITS, default=None,
                    help="F8: unit for the tok/char column (V1: codepoints)")
    return ap


FIX_FLAGS = ("split", "lowercase", "nfc", "aggregate", "special_tokens", "denominator", "char_unit")


def config_from_args(args) -> Config:
    base = V0 if args.v0 else V1
    overrides = {name: getattr(args, name) for name in FIX_FLAGS if getattr(args, name) is not None}
    return replace(base, **overrides)


def main() -> None:
    args = build_parser().parse_args()
    cfg = config_from_args(args)

    # labels follow the units; v0's units give the original wording exactly
    label = "fertility (tok/word)" if cfg.denominator == "words" else f"tokens/{cfg.denominator}"
    char_label = "tok/char" if cfg.char_unit == "codepoints" else f"tok/{cfg.char_unit}"
    measure = "fertility" if cfg.denominator == "words" else f"tokens/{cfg.denominator}"

    encode = load_tokenizer(args.tokenizer)
    print(f"tokenizer: {args.tokenizer}")
    print(f"{'lang':<8}{label:>22}{char_label:>12}")
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
            print(f"{lang} is {ratio:.2f}x the {measure} of {base} "
                  f"({'worse' if ratio > 1 else 'better'} tokenization)")


if __name__ == "__main__":
    main()
