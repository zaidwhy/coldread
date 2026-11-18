"""Step 4 scoring: a reader that follows the list scores 0.5, a reader that reads the text scores 1."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import order_cross  # noqa: E402
import sweep  # noqa: E402

AUTHORS = [(str(i), "male" if i % 2 else "female") for i in range(40)]


def _rows(answer):
    """One step, every author, under both orders; answer(order, truth) is the reader's gender reply."""
    return {
        order: {
            (author, 100): {
                "author_id": author, "n_words": 100,
                "truth": {"gender": truth, "age_band": "13-17", "sign": "Aries"},
                "pred": {"gender": answer(order, truth), "age_band": "13-17", "sign": "Leo"},
            }
            for author, truth in AUTHORS
        }
        for order in order_cross.ORDERS
    }


def test_first_option_picker_scores_half_and_never_clears():
    table = order_cross.reader_table(_rows(lambda order, truth: order_cross.FIRST[order]["gender"]))
    cell = table["cells"][("gender", 100)]
    assert cell["crossed"] == 0.5
    assert cell["follows_position"] == len(AUTHORS)
    assert cell["invariant_correct"] == 0
    assert table["half_life"]["gender"] is None


def test_text_reader_clears_and_is_order_invariant():
    table = order_cross.reader_table(_rows(lambda order, truth: truth))
    cell = table["cells"][("gender", 100)]
    assert cell["crossed"] == 1.0
    assert cell["invariant_correct"] == len(AUTHORS)
    assert table["half_life"]["gender"] == 100 and table["sustained"]["gender"] == 100
    assert table["half_life"]["sign"] is None  # the control answers Leo for authors who are all Aries


def test_mcnemar_counts_discordant_pairs_exactly():
    a = [True] * 10 + [False] * 2
    b = [False] * 8 + [True] * 4
    assert order_cross.mcnemar(a, b) == (8, 2, 2 * (1 + 10 + 45) / 2 ** 10)
    assert order_cross.mcnemar(a, a) == (0, 0, 1.0)


def test_fixed_orders_ignore_the_author_id_and_parity_is_unchanged():
    for author in ("7", "8"):
        assert sweep.option_order(author, sweep.GENDERS, "listed") == ["male", "female"]
        assert sweep.option_order(author, sweep.GENDERS, "reversed") == ["female", "male"]
    assert sweep.option_order("7", sweep.GENDERS) == ["female", "male"]
    assert sweep.option_order("8", sweep.GENDERS) == ["male", "female"]


def test_committed_crossed_rows_reproduce_result_md_step4():
    res = order_cross.run()
    gender = {m: t["half_life"]["gender"] for m, t in res["tables"].items()}
    assert gender == {"llama3.1:8b": 25, "qwen2.5:7b-instruct": 100, "mistral:7b": 50}
    for table in res["tables"].values():
        assert table["half_life"]["age_band"] == 25
        assert table["half_life"]["sign"] is None
        assert all(cell["authors"] == 72 for cell in table["cells"].values())
    alpha = 1 - res["level"]
    for other in ("qwen2.5:7b-instruct", "mistral:7b"):
        gap = res["primary"][other]["gender"]
        assert gap["lo"] > 0  # ahead in the crossed score
        assert gap["listed"][2] > alpha  # not separable with male listed first
        assert gap["reversed"][2] < alpha
        age = res["primary"][other]["age_band"]
        assert age["lo"] < 0 < age["hi"]
