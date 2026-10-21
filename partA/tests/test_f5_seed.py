"""F5: `import random` + `random.seed(1337)` in fertility.py is unused technical debt.

Evidence that removing it is safe, without editing the original:
1. static: the original's AST uses `random` only in that one seed call;
2. dynamic: v0's results are identical whatever the global RNG state is;
3. v1 has no `random` dependency at all.
"""
import ast
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOY = ROOT / "starter_kit" / "corpus_sample"


def random_uses(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    uses = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "random":
            uses.append(node.attr)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names]
            if "random" in names or getattr(node, "module", None) == "random":
                uses.append("import")
    return uses


def test_f5_given_original_source_then_random_is_only_imported_and_seeded():
    assert sorted(random_uses(ROOT / "starter_kit" / "fertility.py")) == ["import", "seed"]


def test_f5_given_v1_source_then_random_is_not_used_at_all():
    assert random_uses(ROOT / "partA" / "fertility_v1.py") == []


@pytest.mark.gpt2
@pytest.mark.parametrize("seed", [0, 1337, 2**31 - 1])
def test_f5_given_any_rng_state_when_v0_runs_then_results_are_identical(seed):
    from audit.v0 import load_v0

    mod = load_v0()  # executes random.seed(1337) at import
    encode = mod.load_tokenizer("gpt2")
    lines = mod.read_lines(str(TOY / "hin_sample.txt"))
    baseline = mod.analyze(lines, encode)
    random.seed(seed)
    random.random()  # perturb the global RNG
    assert mod.analyze(lines, encode) == baseline
