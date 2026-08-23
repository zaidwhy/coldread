"""Did the model memorise the corpus, or is it inferring?

The Blog Authorship Corpus is public and labelled, so a sceptic can argue the
accuracy in RESULT.md is retrieval rather than inference. This probes for the
retrieval directly: feed the model a verbatim prefix of an author's text and ask
it to continue. A model that memorised the corpus will reproduce the real
continuation well above chance.

The control is what makes it readable. Each generated continuation is scored
twice - against that author's true next words, and against a different author's
next words. Overlap is never zero, because English shares function words. Only
the gap between the two means anything.

Usage: python contamination_check.py --model qwen2.5:7b-instruct
"""

import argparse
import json
from pathlib import Path

import requests

ROOT = Path(__file__).parent
SAMPLE = ROOT / "data" / "sample.json"
ENDPOINT = "http://127.0.0.1:11434/api/generate"  # completion, not chat

PREFIX_WORDS = 50
CONTINUE_WORDS = 50
N_AUTHORS = 20
SEED = 1938


def ngrams(words, n=3):
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def overlap(generated, reference, n=3):
    """Fraction of the reference's trigrams that the generation reproduced."""
    ref = ngrams([w.lower() for w in reference], n)
    if not ref:
        return 0.0
    gen = ngrams([w.lower() for w in generated], n)
    return len(ref & gen) / len(ref)


def complete(model, prefix, timeout=600):
    body = {
        "model": model,
        "prompt": prefix,
        "stream": False,
        "raw": True,  # no chat template: we want raw continuation behaviour
        "options": {"temperature": 0, "seed": SEED, "num_predict": 120},
    }
    r = requests.post(ENDPOINT, json=body, timeout=timeout)
    r.raise_for_status()
    return r.json().get("response", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    args = ap.parse_args()

    authors = json.loads(SAMPLE.read_text(encoding="utf-8"))[:N_AUTHORS]

    true_scores, control_scores = [], []
    for i, a in enumerate(authors):
        words = a["text"].split()
        if len(words) < PREFIX_WORDS + CONTINUE_WORDS:
            continue
        prefix = " ".join(words[:PREFIX_WORDS])
        true_next = words[PREFIX_WORDS:PREFIX_WORDS + CONTINUE_WORDS]

        # Control: a different author's continuation, same length.
        other = authors[(i + 1) % len(authors)]["text"].split()
        control_next = other[PREFIX_WORDS:PREFIX_WORDS + CONTINUE_WORDS]

        try:
            gen = complete(args.model, prefix).split()
        except Exception as exc:
            print(f"[{i}] FAILED {type(exc).__name__}: {exc}")
            continue

        t = overlap(gen, true_next)
        c = overlap(gen, control_next)
        true_scores.append(t)
        control_scores.append(c)
        print(f"[{i + 1}/{len(authors)}] true={t:.3f} control={c:.3f}")

    if not true_scores:
        raise SystemExit("no scores collected")

    mt = sum(true_scores) / len(true_scores)
    mc = sum(control_scores) / len(control_scores)
    print(f"\nmodel: {args.model}   authors scored: {len(true_scores)}")
    print(f"mean trigram overlap with TRUE continuation:    {mt:.4f}")
    print(f"mean trigram overlap with CONTROL continuation: {mc:.4f}")
    print(f"gap: {mt - mc:+.4f}")
    print(
        "\nverdict: MEMORISATION LIKELY - the model reproduces real continuations"
        if mt > mc + 0.05 else
        "\nverdict: no memorisation detected - the model does not reproduce this"
        " corpus, so the accuracy in RESULT.md is inference, not retrieval"
    )


if __name__ == "__main__":
    main()
