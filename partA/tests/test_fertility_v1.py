"""fertility_v1.py: corrected script with one flag per audited fix.

Step 4 scenario: Given --v0 settings, when v1 analyzes any corpus, then it
returns exactly the original script's numbers (so every later delta is
caused only by the flag being changed).
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOY = ROOT / "starter_kit" / "corpus_sample"
FLORES = ROOT / "partA" / "corpus" / "prepared"

CORPORA = [TOY / "eng_sample.txt", TOY / "hin_sample.txt"] + [
    FLORES / f"{lang}.{split}.txt"
    for lang in ("eng_Latn", "hin_Deva", "kan_Knda", "tam_Taml")
    for split in ("dev", "devtest")
]


@pytest.fixture(scope="module")
def v0():
    from audit.v0 import load_v0

    return load_v0()


@pytest.fixture(scope="module")
def gpt2(v0):
    return v0.load_tokenizer("gpt2")


@pytest.mark.parametrize("path", CORPORA, ids=lambda p: p.name)
def test_given_v0_config_when_analyzing_then_identical_to_original(path, v0, gpt2):
    import fertility_v1 as v1

    original = v0.analyze(v0.read_lines(str(path)), gpt2)
    got = v1.analyze(v1.read_lines(path, v1.V0), gpt2, v1.V0)
    assert (got["fertility"], got["tok_per_char"]) == original  # exact, not approx


def test_given_v0_flag_when_run_as_cli_then_stdout_matches_original_byte_for_byte():
    args = ["--corpus", f"eng={TOY / 'eng_sample.txt'}", "--corpus", f"hin={TOY / 'hin_sample.txt'}",
            "--tokenizer", "gpt2"]

    def run(script, *extra):
        return subprocess.run([sys.executable, str(script), *args, *extra],
                              capture_output=True, text=True, encoding="utf-8", check=True).stdout

    assert run(ROOT / "partA" / "fertility_v1.py", "--v0") == run(ROOT / "starter_kit" / "fertility.py")
