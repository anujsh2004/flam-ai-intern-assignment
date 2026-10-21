"""partA/A2_results.md is generated from committed JSON, never hand-typed."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS_MD = ROOT / "partA" / "A2_results.md"


def test_given_committed_json_when_rendered_then_committed_markdown_is_identical():
    from audit.report import render

    assert RESULTS_MD.read_text(encoding="utf-8") == render()


def test_given_render_then_sections_follow_the_agreed_order():
    from audit.report import render

    text = render()
    order = ["## 1. Each fix alone", "## 2. Ablation: leave-one-out", "## 3. Cumulative path", "## 4. The instrument"]
    positions = [text.index(h) for h in order]
    assert positions == sorted(positions)


def test_given_render_then_every_finding_and_tokenizer_appears():
    from audit.experiments import FINDINGS
    from audit.report import render

    text = render()
    for name in FINDINGS:
        assert f"### {name}" in text
    for tok in ("gpt2", "xlm-roberta-base", "Llama-3.2-3B"):
        assert tok in text


def test_given_numbers_in_markdown_then_they_come_from_the_json():
    import json

    from audit.report import render

    f1 = json.loads((ROOT / "partA" / "audit" / "results" / "F1_gpt2.json").read_text(encoding="utf-8"))
    kan = f1["delta_pct"]["flores"]["kan"]["fertility"]
    assert f"{kan:+.2f}%" in render()  # +2.78% for F1 Kannada
