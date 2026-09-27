"""Turn the sweep into the curve.

Reports accuracy per attribute at each input size with Wilson score intervals,
and locates the anonymity half-life: the smallest number of words at which the
lower bound of the interval clears chance. The star-sign row is the control and
should never clear it.

Usage: python analyze.py out/results-qwen2.5_3b-instruct.jsonl [--json]
"""

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ATTRS = ["gender", "age_band", "sign"]


def baselines(rows):
    """The bar to beat is the best constant guess, not 1/k.

    The sample is balanced on gender and age band so those come out at 1/2 and
    1/3, but star signs are unevenly distributed - always answering the commonest
    sign scores well above 1/12, and the control has to survive that.
    """
    out = {}
    for attr in ATTRS:
        counts = defaultdict(int)
        for r in rows:
            truth = norm(attr, r["truth"].get(attr))
            if truth is not None:
                counts[truth] += 1
        total = sum(counts.values())
        out[attr] = max(counts.values()) / total if total else 0.0
    return out


def wilson(k, n, z=1.96):
    """Wilson score interval - honest at small n, unlike the normal approximation."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def norm(attr, value):
    if value is None:
        return None
    v = str(value).strip().lower()
    if attr == "sign":
        return v.capitalize()
    return v


def analyse(path):
    """Everything the report shows, as data: per-step accuracy with Wilson bounds, and the half-lives."""
    rows = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    CHANCE = baselines(rows)

    tally = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # attr -> n_words -> [hits, total]
    unparsed = 0
    for r in rows:
        if not r.get("pred"):
            unparsed += 1
            continue
        for attr in ATTRS:
            truth = norm(attr, r["truth"].get(attr))
            pred = norm(attr, r["pred"].get(attr))
            if truth is None:
                continue
            hits, total = tally[attr][r["n_words"]]
            tally[attr][r["n_words"]] = [hits + (pred == truth), total + 1]

    steps = sorted({r["n_words"] for r in rows})
    half_life = {
        attr: next(
            (n for n in steps
             if tally[attr].get(n, [0, 0])[1] > 0
             and wilson(*tally[attr][n])[0] > CHANCE[attr]),
            None,
        )
        for attr in ATTRS
    }
    cells = {}
    for n in steps:
        for attr in ATTRS:
            hits, total = tally[attr].get(n, [0, 0])
            lo, hi = wilson(hits, total)
            cells[(n, attr)] = {"hits": hits, "total": total, "lo": lo, "hi": hi, "clears": total > 0 and lo > CHANCE[attr]}
    return {
        "model": rows[0]["model"] if rows else "?",
        "records": len(rows),
        "unparsed": unparsed,
        "chance": CHANCE,
        "steps": steps,
        "cells": cells,
        "half_life": half_life,
    }


def as_json(a):
    return {
        "model": a["model"],
        "records": a["records"],
        "unparsed": a["unparsed"],
        "best_constant_guess": {k: round(v, 6) for k, v in a["chance"].items()},
        "steps": [
            {
                "words": n,
                **{
                    attr: {
                        "hits": c["hits"],
                        "total": c["total"],
                        "accuracy": round(c["hits"] / c["total"], 6) if c["total"] else None,
                        "wilson_95": [round(c["lo"], 6), round(c["hi"], 6)],
                        "clears_best_constant_guess": c["clears"],
                    }
                    for attr in ATTRS
                    for c in [a["cells"][(n, attr)]]
                },
            }
            for n in a["steps"]
        ],
        "half_life_words": a["half_life"],
    }


def main(path, emit_json=False):
    a = analyse(path)
    if emit_json:
        print(json.dumps(as_json(a), indent=2))
        return
    CHANCE = a["chance"]

    print(f"model: {a['model']}   records: {a['records']}   unparsed: {a['unparsed']}\n")

    lines = []
    header = f"| {'words':>6} | " + " | ".join(f"{x:^22}" for x in ATTRS) + " |"
    lines.append(header)
    lines.append("|" + "-" * 8 + "|" + "|".join(["-" * 24] * len(ATTRS)) + "|")

    for n in a["steps"]:
        row = []
        for attr in ATTRS:
            c = a["cells"][(n, attr)]
            if c["total"] == 0:
                row.append(f"{'-':^22}")
                continue
            mark = "*" if c["clears"] else " "
            row.append(f"{c['hits']/c['total']:5.1%} [{c['lo']:.2f},{c['hi']:.2f}] n={c['total']:<3}{mark}")
        lines.append(f"| {n:>6} | " + " | ".join(row) + " |")

    print("\n".join(lines))
    print("\nbest constant guess: " + ", ".join(f"{x}={CHANCE[x]:.1%}" for x in ATTRS))
    print("* = 95% lower bound clears the best constant guess\n")

    for attr in ATTRS:
        crossing = a["half_life"][attr]
        label = " (CONTROL - should be None)" if attr == "sign" else ""
        print(f"half-life {attr:9}: {crossing if crossing else 'never'} words{label}")


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if x != "--json"]
    main(args[0] if args else "out/results.jsonl", emit_json="--json" in sys.argv[1:])
