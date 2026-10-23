"""Every number in partA/A2_audit.md's evidence index must equal its JSON source,
and every [E#] cited in the text must exist in the index."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "partA" / "A2_audit.md"


def index_rows() -> list[tuple[str, str, str, str]]:
    text = AUDIT.read_text(encoding="utf-8")
    section = text.split("## Evidence index", 1)[1]
    rows = re.findall(r"^\| (E\d+) \| (\S+) \| (\S+) \| (\S+) \|$", section, re.M)
    assert rows, "evidence index is empty"
    return rows


def lookup(file: str, path: str):
    data = json.loads((ROOT / file).read_text(encoding="utf-8"))
    for key in path.split("."):
        data = data[key]
    return data


def formatted_like(quoted: str, value) -> str:
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    is_pct = quoted.endswith("%")
    digits = quoted.rstrip("%").split(".")[1] if "." in quoted else ""
    return f"{value:{'+' if is_pct else ''}.{len(digits)}f}" + ("%" if is_pct else "")


@pytest.mark.parametrize("eid,file,path,quoted", index_rows(), ids=lambda x: x if str(x).startswith("E") else "")
def test_given_evidence_index_entry_then_value_matches_json(eid, file, path, quoted):
    assert formatted_like(quoted, lookup(file, path)) == quoted.replace("−", "-"), eid


def test_given_audit_text_then_every_cited_id_exists_and_ids_are_unique():
    text = AUDIT.read_text(encoding="utf-8")
    ids = [r[0] for r in index_rows()]
    assert len(ids) == len(set(ids))
    body = text.split("## Evidence index", 1)[0]
    cited = set(re.findall(r"E\d+", " ".join(re.findall(r"\[([^\]]*E\d+[^\]]*)\]", body))))
    assert cited - set(ids) == set()


def finding_sections():
    text = AUDIT.read_text(encoding="utf-8").split("## Findings", 1)[1].split("## Interactions", 1)[0]
    return [s for s in re.split(r"^### ", text, flags=re.M) if s.startswith("F")]


@pytest.mark.parametrize("section", finding_sections(), ids=lambda s: s.split(" ", 1)[0])
def test_given_each_finding_then_the_evidence_rule_triplet_is_present(section):
    """Brief: every claim ships with the exact command, before/after numbers, and one sentence
    on why the delta proves it (unverified claimed flaws cost -5)."""
    assert "**Experiment:**" in section and ("python " in section or "pytest" in section), "command"
    assert "**Before → after:**" in section, "before/after numbers"
    assert "**Why the delta proves it:**" in section, "why-sentence"
