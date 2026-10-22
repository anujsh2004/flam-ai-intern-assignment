"""Every number in partB/answers.md's evidence index equals its results.json source, and every
[P#] cited in the text exists in the index."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ANSWERS = ROOT / "partB" / "answers.md"


def index_rows():
    section = ANSWERS.read_text(encoding="utf-8").split("## Evidence index", 1)[1]
    rows = re.findall(r"^\| (P\d+) \| (\S+) \| (\S+) \| (\S+) \|$", section, re.M)
    assert rows, "evidence index is empty"
    return rows


def lookup(file: str, path: str):
    data = json.loads((ROOT / file).read_text(encoding="utf-8"))
    for key in path.split("."):
        data = data[int(key)] if isinstance(data, list) else data[key]
    return data


def formatted_like(quoted: str, value) -> str:
    if isinstance(value, str):
        return value
    digits = quoted.split(".")[1] if "." in quoted else ""
    return f"{value:.{len(digits)}f}"


@pytest.mark.parametrize("pid,file,path,quoted", index_rows(), ids=lambda x: x if str(x).startswith("P") else "")
def test_given_evidence_entry_then_value_matches_json(pid, file, path, quoted):
    assert formatted_like(quoted, lookup(file, path)) == quoted, pid


def test_given_answers_text_then_every_cited_id_exists_and_ids_are_unique():
    ids = [r[0] for r in index_rows()]
    assert len(ids) == len(set(ids))
    body = ANSWERS.read_text(encoding="utf-8").split("## Evidence index", 1)[0]
    cited = set(re.findall(r"P\d+", " ".join(re.findall(r"\[([^\]]*P\d+[^\]]*)\]", body))))
    assert cited - set(ids) == set()
