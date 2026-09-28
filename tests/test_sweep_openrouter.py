"""The OpenRouter reader path of sweep.py, offline: requests.post is replaced, so no key or network is used."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sweep  # noqa: E402


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


REPLY = '{"gender": "female", "age_band": "20s", "sign": "Leo"}'


def test_openrouter_request_matches_the_local_protocol(monkeypatch):
    seen = {}

    def fake_post(url, json=None, timeout=None, headers=None):
        seen.update(url=url, body=json, headers=headers)
        return FakeResponse({"choices": [{"message": {"content": REPLY}}], "usage": {"cost": 0.00012}})

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(sweep.requests, "post", fake_post)
    raw, cost = sweep.ask_openrouter("meta-llama/llama-3.3-70b-instruct", "some words", author_id="42")

    assert raw == REPLY and cost == pytest.approx(0.00012)
    assert seen["url"] == sweep.OPENROUTER_ENDPOINT
    body = seen["body"]
    assert body["temperature"] == 0 and body["seed"] == sweep.SEED and body["max_tokens"] == 200
    # identical prompt to the Ollama path, including the per-author option order
    assert body["messages"][1]["content"] == sweep.build_prompt("some words", "42")
    assert body["messages"][0]["content"] == sweep.SYSTEM
    assert seen["headers"]["Authorization"] == "Bearer test-key"
    assert "test-key" not in json.dumps(body)


def test_missing_key_fails_clearly(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        sweep.ask_openrouter("m", "t")


def test_ollama_request_is_unchanged(monkeypatch):
    seen = {}

    def fake_post(url, json=None, timeout=None):
        seen.update(url=url, body=json)
        return FakeResponse({"message": {"content": REPLY}})

    monkeypatch.setattr(sweep.requests, "post", fake_post)
    assert sweep.ask("llama3.1:8b", "some words", author_id="42") == REPLY
    assert seen["url"] == sweep.ENDPOINT
    assert seen["body"]["options"] == {"temperature": 0, "seed": sweep.SEED}
    assert seen["body"]["format"] == "json"


def test_budget_stops_the_sweep_and_the_file_resumes(monkeypatch, tmp_path):
    authors = [{"author_id": str(i), "text": "word " * 2000, "gender": "Female", "age_band": "20s", "sign": "Leo"}
               for i in range(3)]
    sample = tmp_path / "sample.json"
    sample.write_text(json.dumps(authors), encoding="utf-8")
    monkeypatch.setattr(sweep, "SAMPLE", sample)
    monkeypatch.setattr(sweep, "OUTDIR", tmp_path)
    monkeypatch.setattr(sweep, "WORD_STEPS", [25, 50])
    monkeypatch.setattr(sweep, "ask_openrouter", lambda *a, **k: (REPLY, 0.01))
    out = tmp_path / "run.jsonl"

    monkeypatch.setattr(sys, "argv", ["sweep.py", "--model", "x/y", "--provider", "openrouter",
                                      "--max-usd", "0.025", "--out", str(out)])
    sweep.main()
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3  # stops once 0.03 >= 0.025, before a fourth call
    assert all(r["provider"] == "openrouter" and r["pred"] for r in rows)

    monkeypatch.setattr(sys, "argv", ["sweep.py", "--model", "x/y", "--provider", "openrouter", "--out", str(out)])
    sweep.main()
    assert len(out.read_text(encoding="utf-8").splitlines()) == 6  # resumed: 3 authors x 2 steps
