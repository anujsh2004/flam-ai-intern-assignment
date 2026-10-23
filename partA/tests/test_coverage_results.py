"""Staleness guard for partA/analysis/coverage.json (slow: re-tokenizes all FLORES text 4 times)."""
import json

import pytest


@pytest.mark.flores
@pytest.mark.gpt2
@pytest.mark.llama
def test_given_committed_coverage_when_rebuilt_then_identical():
    from analysis.coverage import OUT, build

    assert json.loads(json.dumps(build())) == json.loads(OUT.read_text(encoding="utf-8"))
