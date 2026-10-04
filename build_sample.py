"""Build a balanced author sample from the Blog Authorship Corpus.

The corpus (Schler et al. 2006) ships one row per post with the author's
self-reported gender, age, industry and star sign. We regroup it per author so
the sweep can hand the model a controlled number of that author's words.

Star sign is retained deliberately: it is a labelled attribute with no causal
link to the text, so it serves as the negative control for the whole study.

Writes data/sample.json.

`python build_sample.py --industry` builds the step-3 sample instead (PLAN.md change log,
2026-10-04): adults only, four industries, balanced on gender and age band within each
industry. Writes data/sample_industry.json.
"""

import json
import random
import sys
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "data"
CSV = DATA / "blogtext.csv"
OUT = DATA / "sample.json"
OUT_INDUSTRY = DATA / "sample_industry.json"

# Enough words to run the whole sweep on every author without padding or reuse.
MAX_SWEEP_WORDS = 1600
MIN_WORDS = 2000
AUTHORS_PER_CELL = 12  # cells are (age group x gender), 3 x 2 = 72 authors
SEED = 1938

# The corpus bins ages into three bands with a gap between them; keep the bands.
AGE_BANDS = [("13-17", 13, 17), ("23-27", 23, 27), ("33-47", 33, 47)]

# Step 3: industry. Adults only, so "Student" does not stand in for the 13-17 band.
INDUSTRIES = ["Education", "Technology", "Arts", "Communications-Media"]
INDUSTRY_BANDS = ["23-27", "33-47"]
AUTHORS_PER_INDUSTRY = 18  # 9 per gender, 9 per age band (cells of 4 or 5)


def age_band(age):
    for name, lo, hi in AGE_BANDS:
        if lo <= age <= hi:
            return name
    return None


def pick_industry(eligible, rng):
    """18 authors per industry, balanced on gender and on age band inside each industry.

    The four (gender x band) cells hold 5, 4, 4, 5 authors, alternating the larger pair
    by industry so no cell is larger overall.
    """
    picked = []
    for i, industry in enumerate(INDUSTRIES):
        sizes = [5, 4, 4, 5] if i % 2 == 0 else [4, 5, 5, 4]
        cells = [(g, b) for g in ("male", "female") for b in INDUSTRY_BANDS]
        for (gender, band), size in zip(cells, sizes):
            cell = [
                a for a in eligible
                if a["topic"] == industry and a["age_band"] == band
                and a["gender"].lower() == gender
            ]
            rng.shuffle(cell)
            if len(cell) < size:
                print(f"WARNING: only {len(cell)} authors for {industry}/{band}/{gender}")
            picked.extend(cell[:size])
    return picked


def main():
    industry_mode = "--industry" in sys.argv[1:]
    if not CSV.exists():
        raise SystemExit(f"missing {CSV} - download it first")

    # 800MB of posts: accumulate per author in chunks rather than loading it all.
    authors = {}
    cols = ["id", "gender", "age", "topic", "sign", "text"]
    reader = pd.read_csv(CSV, usecols=cols, chunksize=200_000, dtype={"id": str})

    for chunk in reader:
        chunk = chunk.dropna(subset=["text", "gender", "age", "sign"])
        for row in chunk.itertuples(index=False):
            a = authors.get(row.id)
            if a is None:
                band = age_band(int(row.age))
                if band is None:
                    continue
                a = authors[row.id] = {
                    "author_id": row.id,
                    "gender": str(row.gender).strip(),
                    "age": int(row.age),
                    "age_band": band,
                    "topic": str(row.topic).strip(),
                    "sign": str(row.sign).strip(),
                    "words": [],
                }
            if len(a["words"]) < MIN_WORDS:
                a["words"].extend(str(row.text).split())

    eligible = [a for a in authors.values() if len(a["words"]) >= MIN_WORDS]

    # Balance the sample so neither attribute can be won by guessing the majority.
    rng = random.Random(SEED)
    picked = []
    if industry_mode:
        picked = pick_industry(eligible, rng)
    else:
        for band, _, _ in AGE_BANDS:
            for gender in ("male", "female"):
                cell = [
                    a for a in eligible
                    if a["age_band"] == band and a["gender"].lower() == gender
                ]
                rng.shuffle(cell)
                if len(cell) < AUTHORS_PER_CELL:
                    print(f"WARNING: only {len(cell)} authors for {band}/{gender}")
                picked.extend(cell[:AUTHORS_PER_CELL])

    for a in picked:
        a["text"] = " ".join(a["words"][:MAX_SWEEP_WORDS])
        del a["words"]

    out = OUT_INDUSTRY if industry_mode else OUT
    out.write_text(json.dumps(picked, indent=1), encoding="utf-8")

    print(f"eligible authors (>={MIN_WORDS} words): {len(eligible)}")
    print(f"sampled: {len(picked)}")
    print("cells:", {
        f"{a['age_band']}/{a['gender']}": 0 for a in picked
    }.keys().__len__(), "distinct")
    signs = {}
    for a in picked:
        signs[a["sign"]] = signs.get(a["sign"], 0) + 1
    print("sign distribution (the control):", dict(sorted(signs.items())))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
