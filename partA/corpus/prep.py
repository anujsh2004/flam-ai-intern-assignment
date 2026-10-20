#!/usr/bin/env python3
"""Prepare the A1 evaluation corpus from FLORES-200 (dev + devtest).

    python partA/corpus/prep.py

Downloads the original archive if absent, verifies its SHA-256, copies the
selected language files byte-for-byte into partA/corpus/prepared/, and writes
manifest.json (counts, provenance, and how many lines NFC normalisation would
change -- measured, but NOT applied).
"""
import hashlib
import json
import tarfile
import unicodedata
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
OUT = HERE / "prepared"

URL = "https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz"
SHA256 = "b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6"
ARCHIVE = RAW / "flores200_dataset.tar.gz"

LANGS = ["eng_Latn", "hin_Deva", "kan_Knda", "tam_Taml"]
SPLITS = ["dev", "devtest"]
LICENSE = "CC-BY-SA 4.0 (stated on https://huggingface.co/datasets/facebook/flores)"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_archive() -> None:
    if not ARCHIVE.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        print(f"downloading {URL}")
        urllib.request.urlretrieve(URL, ARCHIVE)
    got = sha256_of(ARCHIVE)
    if got != SHA256:
        raise SystemExit(f"archive hash mismatch: expected {SHA256}, got {got}")


def split_lines(data: bytes) -> list[str]:
    text = data.decode("utf-8")  # strict: bad bytes must fail loudly
    return text.split("\n")[:-1] if text.endswith("\n") else text.split("\n")


def main() -> None:
    ensure_archive()
    OUT.mkdir(parents=True, exist_ok=True)

    wanted = {f"./flores200_dataset/{s}/{lang}.{s}": f"{lang}.{s}.txt" for s in SPLITS for lang in LANGS}
    wanted |= {f"./flores200_dataset/metadata_{s}.tsv": f"metadata_{s}.tsv" for s in SPLITS}

    nfc = {lang: {} for lang in LANGS}
    counts = {s: {} for s in SPLITS}
    with tarfile.open(ARCHIVE, "r:gz") as tar:
        for member, out_name in wanted.items():
            data = tar.extractfile(member).read()
            (OUT / out_name).write_bytes(data)
            if out_name.startswith("metadata_"):
                continue
            lang, split = out_name.removesuffix(".txt").rsplit(".", 1)
            lines = split_lines(data)
            counts[split][lang] = len(lines)
            nfc[lang][split] = sum(unicodedata.normalize("NFC", s) != s for s in lines)

    manifest = {
        "source": "FLORES-200 (Meta/NLLB), dev + devtest",
        "archive_url": URL,
        "archive_sha256": SHA256,
        "license": LICENSE,
        "languages": LANGS,
        "sentences": counts,
        "nfc_changed_lines": nfc,
        "note": "Prepared text is the raw FLORES text; NFC normalisation is measured, not applied.",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sentences": counts, "nfc_changed_lines": nfc}, indent=2))


if __name__ == "__main__":
    main()
