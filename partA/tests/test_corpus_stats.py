"""Scenario: Given the prepared corpus, when corpus stats are computed, then the
documented numbers are internally consistent (A1 documentation is generated,
not hand-typed)."""
import json
from pathlib import Path

import pytest

STATS = Path(__file__).resolve().parents[1] / "corpus" / "stats.json"
LANGS = ["eng_Latn", "hin_Deva", "kan_Knda", "tam_Taml"]


@pytest.fixture(scope="module")
def stats():
    from corpus.stats import compute_stats

    return compute_stats()


@pytest.mark.flores
def test_domains_sum_to_split_size(stats):
    for split, n in {"dev": 997, "devtest": 1012}.items():
        assert sum(stats["domains"][split].values()) == n


@pytest.mark.flores
def test_articles_are_counted_and_fewer_than_sentences(stats):
    for split in ("dev", "devtest"):
        assert 0 < stats["articles"][split] < stats["sentences"][split]


@pytest.mark.flores
def test_each_language_has_all_units(stats):
    for lang in LANGS:
        units = stats["languages"][lang]
        assert units["sentences"] == 2009
        for key in ("words", "codepoints", "graphemes", "bytes"):
            assert units[key] > 0


@pytest.mark.flores
def test_english_ratio_to_itself_is_one(stats):
    for unit, (point, lo, hi) in stats["ratio_vs_eng"]["eng_Latn"].items():
        assert point == pytest.approx(1.0) and lo == pytest.approx(1.0) and hi == pytest.approx(1.0)


@pytest.mark.flores
def test_clustered_interval_is_reported_alongside_iid(stats):
    ci = stats["bootstrap_codepoint_ratio"]["hin_Deva"]
    assert set(ci) == {"article_clustered", "iid"}


@pytest.mark.parametrize("path", [STATS, STATS.parent / "prepared" / "manifest.json"])
def test_given_generated_json_when_written_then_line_endings_are_lf_on_every_os(path):
    """Path.write_text translates '\\n' to '\\r\\n' on Windows; generated files
    must be byte-identical across platforms."""
    assert b"\r" not in path.read_bytes()


@pytest.mark.flores
def test_committed_stats_file_matches_fresh_computation(stats):
    """Guards against stale numbers in docs: stats.json must equal a recompute."""
    assert json.loads(STATS.read_text(encoding="utf-8")) == json.loads(json.dumps(stats))
