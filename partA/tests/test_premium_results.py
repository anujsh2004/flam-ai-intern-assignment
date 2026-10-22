"""Staleness guard for partA/analysis/results.json (slow: 4 tokenizers x 2,009 sentences x bootstrap).
Kept apart from test_premium.py so targeted mutation runs can use the fast unit tests only;
the normal full suite always runs this."""
import json

import pytest


@pytest.mark.flores
@pytest.mark.gpt2
@pytest.mark.llama
def test_given_committed_a3_results_when_rebuilt_then_identical():
    from analysis.premium import OUT, build

    assert json.loads(json.dumps(build())) == json.loads(OUT.read_text(encoding="utf-8"))
