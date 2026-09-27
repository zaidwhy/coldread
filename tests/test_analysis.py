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
    "out/results-mistral_7b.jsonl": {"model": "mistral:7b", "gender_half_life": 1600},
    # same family as llama3.1:8b at 3B; gender never clears within 1600 words (None = never)
    "out/results-llama3.2_latest.jsonl": {"model": "llama3.2:latest", "gender_half_life": None},
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
    m = re.search(r"half-life gender\s*:\s*(\d+|never) words", out)
    assert m, out
    expected_text = "never" if expected["gender_half_life"] is None else str(expected["gender_half_life"])
    assert m.group(1) == expected_text


@pytest.mark.parametrize("path,expected", RESULTS.items())
def test_json_output_matches_the_table(path, expected, capsys):
    analyze.main(str(ROOT / path), emit_json=True)
    import json

    data = json.loads(capsys.readouterr().out)
    assert data["model"] == expected["model"]
    assert data["half_life_words"]["gender"] == expected["gender_half_life"]
    assert data["half_life_words"]["sign"] is None
    assert all(set(s) >= {"words", "gender", "age_band", "sign"} for s in data["steps"])
