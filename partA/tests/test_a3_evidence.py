"""Every number in partA/A3_analysis.md's evidence index equals its JSON source, and every
[A#] cited in the text exists in the index (as for A2's audit)."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "partA" / "A3_analysis.md"


def index_rows():
    section = ANALYSIS.read_text(encoding="utf-8").split("## Evidence index", 1)[1]
    rows = re.findall(r"^\| (A\d+) \| (\S+) \| (\S+) \| (\S+) \|$", section, re.M)
    assert rows, "evidence index is empty"
    return rows


def lookup(file: str, path: str):
    data = json.loads((ROOT / file).read_text(encoding="utf-8"))
    for key in path.split("."):
        data = data[int(key)] if isinstance(data, list) else data[key]
    return data


def formatted_like(quoted: str, value) -> str:
    digits = quoted.split(".")[1] if "." in quoted else ""
    return f"{value:.{len(digits)}f}"


@pytest.mark.parametrize("aid,file,path,quoted", index_rows(), ids=lambda x: x if str(x).startswith("A") else "")
def test_given_evidence_entry_then_value_matches_json(aid, file, path, quoted):
    assert formatted_like(quoted, lookup(file, path)) == quoted, aid


def test_given_analysis_text_then_every_cited_id_exists_and_ids_are_unique():
    text = ANALYSIS.read_text(encoding="utf-8")
    ids = [r[0] for r in index_rows()]
    assert len(ids) == len(set(ids))
    body = text.split("## Evidence index", 1)[0]
    cited = set(re.findall(r"A\d+", " ".join(re.findall(r"\[([^\]]*A\d+[^\]]*)\]", body))))
    assert cited - set(ids) == set()
