"""partC/memo.md: the brief's 5 labelled sections exist, it stays about one page, and every
quoted number is generated from partC/results.json (formatted exactly as the memo quotes it)."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MEMO = (ROOT / "partC" / "memo.md").read_text(encoding="utf-8")
R = json.loads((ROOT / "partC" / "results.json").read_text(encoding="utf-8"))


def test_memo_has_the_five_labelled_sections_in_order():
    heads = ["## Assumptions", "## Back-of-envelope arithmetic", "## Success metric", "## Kill criterion",
             "## Day-1 experiment"]
    assert [MEMO.index(h) for h in heads] == sorted(MEMO.index(h) for h in heads)


def test_memo_is_about_one_page():
    assert len(re.findall(r"\S+", MEMO)) <= 700


EXPECTED = {
    "hin premium": f"{R['premiums']['hin']:.2f}",
    "kan premium": f"{R['premiums']['kan']:.2f}",
    "reviewer hours": f"{R['reviewer']['hours_in_gpu_window']} h",
    "judgements at 30/60/90": "{:,} / {:,} / {:,}".format(*R["reviewer"]["judgements_by_rate"].values()),
    "week1 spare": f"{R['budget']['60']['week1']['spare']} spare",
    "hin tokens/pair": f"{R['sft']['tokens_per_pair']['hin']:,.0f}",
    "kan tokens/pair": f"{R['sft']['tokens_per_pair']['kan']:,.0f}",
    "SFT tokens": f"{R['sft']['tokens_total'] / 1e6:.1f}M",
    "GPU hours": f"{R['training']['hours']:.1f} GPU-hours",
    "full FT memory": f"{R['memory']['full_ft_states_gb']:.1f} GB",
    "LoRA memory": f"{R['memory']['lora_base_weights_gb']:.1f} GB",
    "rewriter extra decode": f"{R['rewriter']['extra_decode_fraction'] * 100:.0f}%",
    "rewriter capacity loss": f"{R['rewriter']['capacity_loss_fraction'] * 100:.0f}%",
    "CI 70%": f"± {R['ci']['casual_0.70_n200'] * 100:.1f} pts",
    "CI 95%": f"± {R['ci']['meaning_0.95_n200'] * 100:.1f} pts",
}


@pytest.mark.parametrize("name", EXPECTED)
def test_memo_quotes_the_generated_number(name):
    assert EXPECTED[name] in MEMO, (name, EXPECTED[name])


def test_plan_does_not_fit_at_30_per_hour_and_the_memo_says_so():
    assert R["budget"]["30"]["fits"] is False and "At 30/h it does not fit" in MEMO
