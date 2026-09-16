"""Smoke test: the shipped results reproduce the headline of RESULT.md.

Runs analyze.main on each committed JSONL and checks the two claims the write-up rests on:
the star-sign control never clears chance, and the gender half-life differs by reader.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import analyze  # noqa: E402

RESULTS = {
    "out/results-qwen2.5_7b-instruct.jsonl": {"model": "qwen2.5:7b-instruct", "gender_half_life": 800},
    "out/results-llama3.1_8b.jsonl": {"model": "llama3.1:8b", "gender_half_life": 50},
}


def _run(path: str, capsys) -> str:
    analyze.main(str(ROOT / path))
    return capsys.readouterr().out


@pytest.mark.parametrize("path,expected", RESULTS.items())
def test_control_never_clears_chance(path, expected, capsys):
    out = _run(path, capsys)
    assert expected["model"] in out
    m = re.search(r"half-life sign\s*:\s*(\S+) words", out)
    assert m, out
    assert m.group(1) == "never"


@pytest.mark.parametrize("path,expected", RESULTS.items())
def test_gender_half_life_matches_result_md(path, expected, capsys):
    out = _run(path, capsys)
    m = re.search(r"half-life gender\s*:\s*(\d+) words", out)
    assert m, out
    assert int(m.group(1)) == expected["gender_half_life"]
