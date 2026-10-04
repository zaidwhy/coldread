"""Step 3 (industry as a fourth attribute): sample balance, prompt, and analysis."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import analyze  # noqa: E402
import build_sample  # noqa: E402
import sweep  # noqa: E402


def _authors():
    out = []
    n = 0
    for industry in build_sample.INDUSTRIES + ["Student", "Law"]:
        for gender in ("male", "female"):
            for band in ("13-17", "23-27", "33-47"):
                for _ in range(8):
                    n += 1
                    out.append({"author_id": str(n), "topic": industry, "gender": gender, "age_band": band})
    return out


def test_industry_sample_is_balanced_adult_and_only_the_four_industries():
    picked = build_sample.pick_industry(_authors(), random.Random(1))
    assert len(picked) == 72
    for industry in build_sample.INDUSTRIES:
        group = [a for a in picked if a["topic"] == industry]
        assert len(group) == 18
        assert sum(a["gender"] == "male" for a in group) == 9
        assert sum(a["age_band"] == "23-27" for a in group) == 9
    assert {a["age_band"] for a in picked} == {"23-27", "33-47"}
    assert {a["topic"] for a in picked} == set(build_sample.INDUSTRIES)


def test_industry_prompt_asks_industry_and_sign_only_and_lists_every_option():
    prompt = sweep.build_prompt("some words", "7", task="industry")
    assert '"industry"' in prompt and '"sign"' in prompt
    assert "gender" not in prompt and "age_band" not in prompt
    assert all(f'"{i}"' in prompt for i in sweep.INDUSTRIES)
    assert prompt == sweep.build_prompt("some words", "7", task="industry")  # deterministic


def test_industry_option_order_is_counterbalanced_across_authors():
    firsts = {sweep.build_prompt("t", str(i), task="industry").split('"industry": ')[1].split('"')[1] for i in range(1, 5)}
    assert len(firsts) == 2  # both ends of the list appear first for some author


def _rows(steps, industry_right, sign_right):
    rows = []
    for n in steps:
        for i in range(24):
            truth = {"industry": "Arts", "sign": "Leo"}
            pred = {
                "industry": "Arts" if i < industry_right[n] else "Education",
                "sign": "Leo" if i < sign_right[n] else "Aries",
            }
            rows.append({"author_id": str(i), "n_words": n, "model": "m", "truth": truth, "pred": pred, "error": None})
    return rows


def test_analysis_reports_industry_and_keeps_sign_as_the_control(tmp_path):
    rows = _rows([25, 800], {25: 6, 800: 24}, {25: 3, 800: 3})
    # make the truth set varied so the best constant guess is 25% for industry
    for i, r in enumerate(rows):
        r["truth"]["industry"] = ["Arts", "Education", "Technology", "Communications-Media"][i % 4]
        r["pred"]["industry"] = r["truth"]["industry"] if r["n_words"] == 800 else "Arts"
    path = tmp_path / "r.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")

    a = analyze.analyse(path)

    assert a["attrs"] == ["industry", "sign"]
    assert a["chance"]["industry"] == 0.25
    assert a["half_life"]["industry"] == 800
    assert a["half_life"]["sign"] is None
    assert [k for k in analyze.as_json(a)["steps"][0] if k != "words"] == ["industry", "sign"]


def test_profile_files_still_report_gender_age_and_sign():
    a = analyze.analyse(ROOT / "out" / "results-llama3.1_8b.jsonl")
    assert a["attrs"] == ["gender", "age_band", "sign"]


def test_industry_ollama_call_caps_output_length_and_the_profile_task_does_not(monkeypatch):
    sent = []

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "{}"}}

    monkeypatch.setattr(sweep.requests, "post", lambda url, json=None, timeout=None: sent.append(json) or _Resp())
    sweep.ask("m", "text", "1", task="industry")
    sweep.ask("m", "text", "1")
    assert sent[0]["options"]["num_predict"] == 200
    assert "num_predict" not in sent[1]["options"]


INDUSTRY_RESULTS = {
    "out/results-industry-qwen2.5_7b-instruct.jsonl": 50,
    "out/results-industry-mistral_7b.jsonl": 50,
    "out/results-industry-llama3.1_8b.jsonl": 25,
    "out/results-industry-llama3.2_latest.jsonl": 200,
}


def test_shipped_industry_results_reproduce_the_headline_and_the_control_never_clears():
    for path, expected in INDUSTRY_RESULTS.items():
        a = analyze.analyse(ROOT / path)
        assert a["attrs"] == ["industry", "sign"], path
        assert a["records"] == 504, path
        assert a["chance"] == {"industry": 0.25, "sign": 0.125}, path
        assert a["half_life"]["industry"] == expected, path
        assert a["half_life"]["sign"] is None, path
