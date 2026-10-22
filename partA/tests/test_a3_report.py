"""partA/A3_results.md is generated from partA/analysis/results.json, never hand-typed."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_given_committed_json_when_rendered_then_committed_markdown_is_identical():
    from analysis.report import OUT, render

    assert OUT.read_text(encoding="utf-8") == render()


def test_given_render_then_decision_number_comes_first_and_all_sections_follow():
    from analysis.report import render

    text = render()
    order = ["## 1. Premium per parallel sentence", "## 2. Same tokens, five denominators",
             "## 3. Per-request overhead", "## 4. Spread of per-sentence premiums", "## 5. Token totals"]
    positions = [text.index(h) for h in order]
    assert positions == sorted(positions)


def test_given_render_then_quoted_ci_is_formatted_from_the_json():
    from analysis.report import render

    r = json.loads((ROOT / "partA" / "analysis" / "results.json").read_text(encoding="utf-8"))
    p, lo, hi = r["by_tokenizer"]["llama"]["premium"]["kan"]["sentence"]
    assert f"{p:.3f} [{lo:.3f}, {hi:.3f}]" in render()  # 8.868 [8.774, 8.959]
    o = r["by_tokenizer"]["llama"]["premium_with_overhead"]["hin"][0]
    assert f"→ {o:.3f}" in render()
