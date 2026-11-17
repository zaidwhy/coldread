"""Step 4: every author under both option orders (PLAN.md change log, 2026-11-18).

The original sweeps gave each option order to different authors, so a reader that follows the
list position could not be told apart from a reader that reads the text. Here each author has a
`listed` row and a `reversed` row at every step, and an author's crossed accuracy is the mean of
the two. A pure first-option picker scores exactly 0.5 on gender.

Usage: python order_cross.py [--json]
Reads out/results-crossed-{listed,reversed}-<reader>.jsonl for the three 7-8B readers.
"""

import json
import math
import random
import sys
from pathlib import Path

from analyze import baselines, norm

OUT = Path(__file__).parent / "out"
READERS = ["llama3.1:8b", "qwen2.5:7b-instruct", "mistral:7b"]
REFERENCE = "llama3.1:8b"
ATTRS = ["gender", "age_band", "sign"]
# The option each order lists first, per attribute (sweep.py GENDERS, BANDS, SIGNS).
FIRST = {
    "listed": {"gender": "male", "age_band": "13-17", "sign": "Aries"},
    "reversed": {"gender": "female", "age_band": "33-47", "sign": "Pisces"},
}
ORDERS = ["listed", "reversed"]
PRIMARY_STEP = 1600
BOOT = 10_000
SEED = 1938


def slug(model):
    return model.replace(":", "_").replace("/", "_")


def load(path):
    """(author_id, n_words) -> record, parsed rows only."""
    rows = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("pred"):
                rows[(r["author_id"], r["n_words"])] = r
    return rows


def hit(rec, attr):
    return norm(attr, rec["pred"].get(attr)) == norm(attr, rec["truth"].get(attr))


def boot_interval(values, level=0.95, rng=None):
    """Percentile bootstrap interval of the mean, resampling authors."""
    rng = rng or random.Random(SEED)
    n = len(values)
    means = sorted(sum(rng.choices(values, k=n)) / n for _ in range(BOOT))
    tail = (1 - level) / 2
    return means[int(tail * BOOT)], means[min(BOOT - 1, int((1 - tail) * BOOT))]


def mcnemar(a_hits, b_hits):
    """Exact two-sided McNemar on paired booleans. Returns (a only, b only, p)."""
    a_only = sum(1 for a, b in zip(a_hits, b_hits) if a and not b)
    b_only = sum(1 for a, b in zip(a_hits, b_hits) if b and not a)
    n = a_only + b_only
    if n == 0:
        return 0, 0, 1.0
    tail = sum(math.comb(n, i) for i in range(min(a_only, b_only) + 1)) / 2 ** n
    return a_only, b_only, min(1.0, 2 * tail)


def reader_table(by_order):
    """Per attribute and step: crossed accuracy with its interval, per-order hits, invariance, position following."""
    steps = sorted({n for rows in by_order.values() for _, n in rows})
    chance = baselines(list(by_order["listed"].values()), ATTRS)
    cells, scores = {}, {}
    for attr in ATTRS:
        for n in steps:
            authors = sorted(a for a, s in by_order["listed"] if s == n and (a, n) in by_order["reversed"])
            pair = [(by_order["listed"][(a, n)], by_order["reversed"][(a, n)]) for a in authors]
            crossed = [(hit(l, attr) + hit(r, attr)) / 2 for l, r in pair]
            lo, hi = boot_interval(crossed)
            cells[(attr, n)] = {
                "authors": len(pair),
                "crossed": sum(crossed) / len(crossed),
                "lo": lo,
                "hi": hi,
                "clears": lo > chance[attr],
                "listed_hits": sum(hit(l, attr) for l, _ in pair),
                "reversed_hits": sum(hit(r, attr) for _, r in pair),
                "invariant_correct": sum(hit(l, attr) and hit(r, attr) for l, r in pair),
                "follows_position": sum(
                    norm(attr, l["pred"].get(attr)) == FIRST["listed"][attr]
                    and norm(attr, r["pred"].get(attr)) == FIRST["reversed"][attr]
                    for l, r in pair
                ),
            }
            scores[(attr, n)] = dict(zip(authors, crossed))
    half_life, sustained = {}, {}
    for attr in ATTRS:
        clears = [cells[(attr, n)]["clears"] for n in steps]
        half_life[attr] = next((n for n, c in zip(steps, clears) if c), None)
        sustained[attr] = next((n for i, n in enumerate(steps) if all(clears[i:])), None)
    return {"steps": steps, "chance": chance, "cells": cells, "scores": scores,
            "half_life": half_life, "sustained": sustained}


def compare(ref, other, ref_rows, other_rows, attr, n, level):
    """Reference reader against another at one step: crossed difference and one McNemar per order."""
    authors = sorted(set(ref["scores"][(attr, n)]) & set(other["scores"][(attr, n)]))
    diffs = [ref["scores"][(attr, n)][a] - other["scores"][(attr, n)][a] for a in authors]
    lo, hi = boot_interval(diffs, level)
    out = {"authors": len(authors), "diff": sum(diffs) / len(diffs), "lo": lo, "hi": hi}
    for order in ORDERS:
        keys = [(a, n) for a in authors]
        out[order] = mcnemar([hit(ref_rows[order][k], attr) for k in keys],
                             [hit(other_rows[order][k], attr) for k in keys])
    return out


def repeat_check(model, by_order):
    """Committed parity rows against the fresh row with the same author, step and order."""
    path = OUT / f"results-{slug(model)}.jsonl"
    if not path.exists():
        return None
    same = total = 0
    for (author, n), old in load(path).items():
        order = "reversed" if sum(ord(c) for c in str(author)) % 2 == 1 else "listed"
        new = by_order[order].get((author, n))
        if new is None:
            continue
        total += 1
        same += norm("gender", old["pred"].get("gender")) == norm("gender", new["pred"].get("gender"))
    return {"rows": total, "same_gender": same}


def run():
    rows = {m: {o: load(OUT / f"results-crossed-{o}-{slug(m)}.jsonl") for o in ORDERS} for m in READERS}
    tables = {m: reader_table(rows[m]) for m in READERS}
    others = [m for m in READERS if m != REFERENCE]
    level = 1 - 0.05 / len(others)
    primary = {m: {a: compare(tables[REFERENCE], tables[m], rows[REFERENCE], rows[m], a, PRIMARY_STEP, level)
                   for a in ("gender", "age_band")} for m in others}
    by_step = {m: {n: compare(tables[REFERENCE], tables[m], rows[REFERENCE], rows[m], "gender", n, 0.95)
                   for n in tables[m]["steps"]} for m in others}
    return {"tables": tables, "primary": primary, "by_step": by_step, "level": level,
            "repeat": {m: repeat_check(m, rows[m]) for m in READERS}}


def report(res):
    for model, t in res["tables"].items():
        print(f"\n== {model}")
        for attr in ATTRS:
            role = " (control)" if attr == "sign" else ""
            print(f"{attr}{role}: bar {t['chance'][attr]:.3f} | crossed half-life {t['half_life'][attr]} "
                  f"| sustained {t['sustained'][attr]}")
            print("  words  crossed  95% interval    listed  reversed  same+right  follows-list  authors")
            for n in t["steps"]:
                c = t["cells"][(attr, n)]
                flag = "*" if c["clears"] else " "
                print(f"  {n:>5}  {c['crossed']:.3f}{flag}  [{c['lo']:.3f}, {c['hi']:.3f}]  "
                      f"{c['listed_hits']:>6}  {c['reversed_hits']:>8}  {c['invariant_correct']:>10}  "
                      f"{c['follows_position']:>12}  {c['authors']:>7}")
        rep = res["repeat"][model]
        if rep:
            print(f"repeat check: {rep['same_gender']} of {rep['rows']} committed parity-order gender predictions "
                  f"match the fresh row with the same order")

    pct = res["level"] * 100
    print(f"\n== primary test at {PRIMARY_STEP} words: {REFERENCE} minus other ({pct:.1f}% intervals, p judged against "
          f"{(1 - res['level']):.3f})")
    for model, per_attr in res["primary"].items():
        for attr, c in per_attr.items():
            line = f"{attr:<8} vs {model:<20} crossed diff {c['diff']:+.3f} [{c['lo']:+.3f}, {c['hi']:+.3f}]"
            for order in ORDERS:
                ref_only, other_only, p = c[order]
                line += f" | {order}: {ref_only} vs {other_only}, p={p:.4f}"
            print(line)

    print("\n== gender at every step, uncorrected (95% intervals)")
    for model, steps in res["by_step"].items():
        for n, c in steps.items():
            line = f"vs {model:<20} {n:>5} words  crossed diff {c['diff']:+.3f} [{c['lo']:+.3f}, {c['hi']:+.3f}]"
            for order in ORDERS:
                line += f" | {order} p={c[order][2]:.4f}"
            print(line)


def as_json(res):
    def table(t):
        return {"chance": t["chance"], "half_life_words": t["half_life"], "sustained_half_life_words": t["sustained"],
                "cells": [{"attr": a, "n_words": n, **c} for (a, n), c in t["cells"].items()]}
    return {
        "readers": {m: table(t) for m, t in res["tables"].items()},
        "primary": res["primary"],
        "by_step": {m: {str(n): c for n, c in steps.items()} for m, steps in res["by_step"].items()},
        "interval_level_primary": res["level"],
        "repeat_check": res["repeat"],
    }


if __name__ == "__main__":
    result = run()
    if "--json" in sys.argv:
        print(json.dumps(as_json(result), indent=2))
    else:
        report(result)
