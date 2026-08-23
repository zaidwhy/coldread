"""Build a balanced author sample from the Blog Authorship Corpus.

The corpus (Schler et al. 2006) ships one row per post with the author's
self-reported gender, age, industry and star sign. We regroup it per author so
the sweep can hand the model a controlled number of that author's words.

Star sign is retained deliberately: it is a labelled attribute with no causal
link to the text, so it serves as the negative control for the whole study.

Writes data/sample.json.
"""

import json
import random
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "data"
CSV = DATA / "blogtext.csv"
OUT = DATA / "sample.json"

# Enough words to run the whole sweep on every author without padding or reuse.
MAX_SWEEP_WORDS = 1600
MIN_WORDS = 2000
AUTHORS_PER_CELL = 12  # cells are (age group x gender), 3 x 2 = 72 authors
SEED = 1938

# The corpus bins ages into three bands with a gap between them; keep the bands.
AGE_BANDS = [("13-17", 13, 17), ("23-27", 23, 27), ("33-47", 33, 47)]


def age_band(age):
    for name, lo, hi in AGE_BANDS:
        if lo <= age <= hi:
            return name
    return None


def main():
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

    OUT.write_text(json.dumps(picked, indent=1), encoding="utf-8")

    print(f"eligible authors (>={MIN_WORDS} words): {len(eligible)}")
    print(f"sampled: {len(picked)}")
    print("cells:", {
        f"{a['age_band']}/{a['gender']}": 0 for a in picked
    }.keys().__len__(), "distinct")
    signs = {}
    for a in picked:
        signs[a["sign"]] = signs.get(a["sign"], 0) + 1
    print("sign distribution (the control):", dict(sorted(signs.items())))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
