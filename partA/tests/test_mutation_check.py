"""The mutation checker itself must survive non-ASCII pytest output.

Regression: a mutant's failing assertion printed Devanagari; reading the child
pytest's output as cp1252 (Windows default) crashed the whole run.
"""


def test_given_current_code_then_every_mutant_snippet_occurs_exactly_once():
    """Fail fast: a stale mutant used to abort a 25-minute run midway (F6 step)."""
    from audit.mutation_check import MUTANTS, ROOT

    stale = []
    for name, rel, old, _new in MUTANTS:
        count = (ROOT / rel).read_text(encoding="utf-8").count(old)
        if count != 1:
            stale.append((name, rel, count))
    assert stale == []


def test_given_failing_test_with_devanagari_output_when_run_then_counts_are_parsed(tmp_path, monkeypatch):
    from audit.mutation_check import run_tests

    # the crashing run had PYTHONIOENCODING=utf-8, so the child wrote UTF-8 bytes
    monkeypatch.setenv("PYTHONIOENCODING", "utf-8")
    (tmp_path / "test_x.py").write_text(
        'def test_ok():\n    assert True\n\n'
        # U+0941 (vowel sign u) is E0 A5 81 in UTF-8; 0x81 is undefined in cp1252
        'def test_hindi():\n    assert "बु" == "ज़"\n',
        encoding="utf-8",
    )
    code, passed = run_tests(tmp_path, ["test_x.py"])
    assert code != 0 and passed == 1
