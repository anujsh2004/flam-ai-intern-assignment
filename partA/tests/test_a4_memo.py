"""partA/A4_memo.md: the four required parts, about one page, and every quoted number generated
from the committed JSON (A3 results, coverage, A2 F9 results)."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MEMO = (ROOT / "partA" / "A4_memo.md").read_text(encoding="utf-8")
P = json.loads((ROOT / "partA" / "analysis" / "results.json").read_text(encoding="utf-8"))["by_tokenizer"]
C = json.loads((ROOT / "partA" / "analysis" / "coverage.json").read_text(encoding="utf-8"))["by_tokenizer"]
F9 = json.loads((ROOT / "partA" / "audit" / "results" / "F9_v0.json").read_text(encoding="utf-8"))


def test_memo_has_the_four_required_parts_in_order():
    heads = ["## Corrected headline numbers", "## Routing recommendation", "## Biggest caveat",
             "## The one metric to monitor in production"]
    assert [MEMO.index(h) for h in heads] == sorted(MEMO.index(h) for h in heads)


def test_memo_is_about_one_page():
    assert len(re.findall(r"\S+", MEMO)) <= 650


def ci(cell):
    p, lo, hi = cell
    return f"**{p:.2f}×** [{lo:.2f}, {hi:.2f}]"


EXPECTED = {
    "hin headline": ci(P["llama"]["premium"]["hin"]["sentence"]),
    "kan headline": ci(P["llama"]["premium"]["kan"]["sentence"]),
    "tam headline": ci(P["llama"]["premium"]["tam"]["sentence"]),
    "report 5.89": f"{F9['a']['toy']['hin']['fertility_ratio_vs_eng']:.2f}×",
    "report metric with proxy": f"{F9['b']['flores']['hin']['fertility_ratio_vs_eng']:.2f}×",
    "kan fragments": f"**{C['llama']['by_lang']['kan']['fragment_share'] * 100:.1f}%**",
    "tam fragments": f"**{C['llama']['by_lang']['tam']['fragment_share'] * 100:.1f}%**",
    "hin fragments": f"{C['llama']['by_lang']['hin']['fragment_share'] * 100:.1f}%",
    "kan length": f"{C['llama']['by_lang']['kan']['codepoints_vs_eng']:.2f}×",
    "tam length": f"{C['llama']['by_lang']['tam']['codepoints_vs_eng']:.2f}×",
    "indicbert kan": f"{P['indicbert']['premium']['kan']['sentence'][0]:.2f}×",
    "hin range low": f"{P['indicbert']['premium']['hin']['sentence'][0]:.2f}×",
    "hin range high": f"{P['gpt2']['premium']['hin']['sentence'][0]:.2f}×",
    "kan range high": f"{P['gpt2']['premium']['kan']['sentence'][0]:.2f}×",
    "baseline eng": f"English {C['llama']['by_lang']['eng']['tokens_per_codepoint']:.2f}",
    "baseline hin": f"Hindi {C['llama']['by_lang']['hin']['tokens_per_codepoint']:.2f}",
    "baseline kan": f"Kannada {C['llama']['by_lang']['kan']['tokens_per_codepoint']:.2f}",
    "baseline tam": f"Tamil {C['llama']['by_lang']['tam']['tokens_per_codepoint']:.2f}",
}


@pytest.mark.parametrize("name", EXPECTED)
def test_memo_quotes_the_generated_number(name):
    assert EXPECTED[name] in MEMO, (name, EXPECTED[name])
