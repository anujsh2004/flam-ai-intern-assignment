import sys
from pathlib import Path

import pytest

# make partA/ importable as a flat package root (units.py, corpus/...)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from testsupport import missing_flores, missing_gpt2  # noqa: E402

CHECKS = {"flores": missing_flores, "gpt2": missing_gpt2}


def pytest_configure(config):
    config.addinivalue_line("markers", "flores: needs FLORES text from partA/corpus/prep.py")
    config.addinivalue_line("markers", "gpt2: needs the tiktoken gpt2 encoding (network on first use)")


def pytest_runtest_setup(item):
    # skip (never pass) when an ungitted resource is absent, naming the fix
    for name, check in CHECKS.items():
        if item.get_closest_marker(name) and (reason := check()):
            pytest.skip(reason)
