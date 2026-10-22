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


def test_given_targeted_options_then_only_mutants_in_those_files_and_those_tests_are_used():
    """Targeted run (user request, A3): mutants filtered by file, tests by path; default stays full."""
    from audit.mutation_check import MUTANTS, TESTS, parse_args, select

    full = select(parse_args([]))
    assert full == (MUTANTS, TESTS)
    mutants, tests = select(parse_args(["--files", "partA/analysis/premium.py", "--tests", "partA/tests/test_premium.py"]))
    assert mutants and all(rel == "partA/analysis/premium.py" for _, rel, _, _ in mutants)
    assert tests == ["partA/tests/test_premium.py"]
    # by name prefix: picks A3 mutants across files without pulling in A2 mutants of the same file
    mutants, _ = select(parse_args(["--names", "A3", "--tests", "partA/tests/test_premium.py"]))
    assert mutants and all(name.startswith("A3") for name, _, _, _ in mutants)
    assert {rel for _, rel, _, _ in mutants} == {"partA/analysis/premium.py", "partA/audit/experiments.py"}


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
