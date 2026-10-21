"""BDD-style tests for the A1 evaluation corpus (FLORES-200 dev + devtest).

Run from the repo root:  .venv/Scripts/python -m pytest partA/tests/test_corpus.py -v

Each test is a Given/When/Then scenario. Thresholds marked PROVISIONAL are
sanity bands chosen before looking at the data; they are reported and, if
wrong, revised openly in NOTEBOOK.md rather than silently loosened.
"""
import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.flores  # reads prepared FLORES text

PREPARED = Path(__file__).resolve().parents[1] / "corpus" / "prepared"
LANGS = {"eng": "eng_Latn", "hin": "hin_Deva", "kan": "kan_Knda", "tam": "tam_Taml"}
EXPECTED_COUNTS = {"dev": 997, "devtest": 1012}
ARCHIVE_SHA256 = "b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6"


def read_lines(lang, split):
    # strict UTF-8: a decoding problem must fail the test, not be hidden
    text = (PREPARED / f"{LANGS[lang]}.{split}.txt").read_text(encoding="utf-8")
    return text.split("\n")[:-1] if text.endswith("\n") else text.split("\n")


@pytest.mark.parametrize("split", EXPECTED_COUNTS)
def test_given_four_languages_when_loaded_then_counts_match_flores_and_each_other(split):
    counts = {lang: len(read_lines(lang, split)) for lang in LANGS}
    assert set(counts.values()) == {EXPECTED_COUNTS[split]}, counts


@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize("split", EXPECTED_COUNTS)
def test_given_a_language_when_read_then_no_blank_lines(lang, split):
    blank = [i for i, line in enumerate(read_lines(lang, split)) if not line.strip()]
    assert blank == []


@pytest.mark.parametrize("split", EXPECTED_COUNTS)
def test_given_metadata_when_loaded_then_one_row_per_sentence(split):
    rows = (PREPARED / f"metadata_{split}.tsv").read_text(encoding="utf-8").splitlines()
    header, body = rows[0].split("\t"), rows[1:]
    assert header[:2] == ["URL", "domain"]
    assert len(body) == EXPECTED_COUNTS[split]


@pytest.mark.parametrize("lang", ["hin", "kan", "tam"])
def test_given_parallel_lines_when_compared_to_english_then_lengths_are_plausible(lang):
    """PROVISIONAL band: <=1% of lines may have a char-length ratio outside [0.2, 5].
    Catches shifted/misaligned files; does not prove alignment."""
    out_of_band = total = 0
    for split in EXPECTED_COUNTS:
        for en, other in zip(read_lines("eng", split), read_lines(lang, split)):
            total += 1
            if not 0.2 <= len(other) / len(en) <= 5:
                out_of_band += 1
    assert out_of_band / total <= 0.01, (out_of_band, total)


@pytest.mark.parametrize("lang", ["hin", "kan", "tam"])
def test_given_parallel_lines_when_english_has_numbers_then_most_appear_in_translation(lang):
    """PROVISIONAL: >=60% of English lines containing a multi-digit number must
    contain at least one of those numbers (ASCII digits) in the translation."""
    hits = checked = 0
    for split in EXPECTED_COUNTS:
        for en, other in zip(read_lines("eng", split), read_lines(lang, split)):
            nums = re.findall(r"\d{2,}", en)
            if nums:
                checked += 1
                hits += any(n in other for n in nums)
    assert checked > 50, checked
    assert hits / checked >= 0.60, (hits, checked)


def test_given_the_manifest_when_read_then_it_records_provenance_and_nfc_effect():
    m = json.loads((PREPARED / "manifest.json").read_text(encoding="utf-8"))
    assert m["archive_sha256"] == ARCHIVE_SHA256
    assert "CC-BY-SA" in m["license"]
    for lang in LANGS:
        for split in EXPECTED_COUNTS:
            assert isinstance(m["nfc_changed_lines"][LANGS[lang]][split], int)


@pytest.mark.parametrize("lang", LANGS)
def test_given_prepared_text_when_nfc_changes_lines_then_manifest_count_is_correct(lang):
    """The manifest NFC count must match an independent recount (guards against a
    wrong report). Prepared text itself is stored unnormalised (raw)."""
    import unicodedata

    m = json.loads((PREPARED / "manifest.json").read_text(encoding="utf-8"))
    for split in EXPECTED_COUNTS:
        recount = sum(unicodedata.normalize("NFC", s) != s for s in read_lines(lang, split))
        assert m["nfc_changed_lines"][LANGS[lang]][split] == recount
