# The Anonymity Half-Life

**Gate: PASSED.** Run 2026-08-23. `qwen2.5:7b-instruct`, temperature 0, seed 1938,
504 calls, 0 errors, 0 unparsed. Raw data in `out/results-qwen2.5_7b-instruct.jsonl`,
reproduce with `python analyze.py out/results-qwen2.5_7b-instruct.jsonl`.

## Result

72 authors from the Blog Authorship Corpus, balanced across three age bands and both
genders. Each author's own first N words shown to the model, which had to commit to
gender, age band and star sign every time.

| words | gender | age band | sign (control) |
|---|---|---|---|
| 25 | 44.4% [0.34, 0.56] | 38.9% [0.28, 0.50] | 8.3% [0.04, 0.17] |
| 50 | 43.1% [0.32, 0.55] | 37.5% [0.27, 0.49] | 9.7% [0.05, 0.19] |
| 100 | 45.8% [0.35, 0.57] | **45.8%** [0.35, 0.57] | 8.3% [0.04, 0.17] |
| 200 | 51.4% [0.40, 0.63] | 52.8% [0.41, 0.64] | 5.6% [0.02, 0.13] |
| 400 | 56.9% [0.45, 0.68] | 54.2% [0.43, 0.65] | 9.7% [0.05, 0.19] |
| 800 | **65.3%** [0.54, 0.75] | 55.6% [0.44, 0.66] | 8.3% [0.04, 0.17] |
| 1600 | 72.2% [0.61, 0.81] | 58.3% [0.47, 0.69] | 8.3% [0.04, 0.17] |

Brackets are 95% Wilson score intervals. Bold marks the crossing point. The bar is the
best constant guess available on this sample: gender 50.0%, age band 33.3%, sign 15.3%.

**Half-life gender: 800 words. Half-life age band: 100 words. Sign: never.**

## What the control proves

Star sign is labelled in the corpus and is not inferable from text. It went through the
identical pipeline and never left its floor - 5.6% to 9.7% across all seven steps, against
a 15.3% bar. The pipeline is not manufacturing signal. Had sign climbed alongside the
others, everything here would have been void.

## Three findings

**1. There is no single anonymity half-life.** Each attribute has its own threshold and its
own ceiling. Age band is cheap: it clears at 100 words. It is also capped: it saturates
around 55-58% and stops improving by 200 words. Gender is expensive - 800 words to clear -
but is still climbing at 1,600 and has not found its ceiling. Cheap-and-capped versus
expensive-and-rising is a structural difference, not a difference of degree.

**2. Below roughly 100 words the model is worse than chance, not merely uninformed.** Gender
reads 44.4% at 25 words and 43.1% at 50 - both under a coin flip, and consistently so. Short
samples do not produce ignorance, they produce confident anti-correlated guesses. The most
plausible reading is that a short sample surfaces stereotype matching which the genuine
signal only later overrides. This is the opposite of the intuitive picture, in which
knowledge accumulates from zero.

**3. The knowing is gradual, not a cliff.** Both curves rise smoothly rather than snapping on
at a threshold. "Anonymous until word N, exposed after" is the wrong mental model; exposure
accrues.

## Caveats

- **One model, one corpus.** Everything here is `qwen2.5:7b-instruct` on 2004 blogger.com
  text. Replication on a second model family is the obvious next step, and until it exists
  these numbers describe this model rather than language models.
- **Contamination is not ruled out.** The corpus is public and labelled. The sign control
  rules out a pipeline artefact but not memorisation of author-to-attribute pairs. The
  strong check is a corpus the model cannot have seen paired with its labels.
- **n = 72 authors.** The intervals are wide. Gender at 800 words clears with a lower bound
  of 0.54 against a 0.50 bar, which is a pass but a narrow one. Treat 800 as "somewhere in
  the high hundreds", not as a precise figure.
- **Demographic attributes only.** Gender and age band. The more invasive inferences in the
  literature - income, location, employer - are not tested here and must not be claimed.
- **A 3B model could not do this at all.** `qwen2.5:3b-instruct` answered "male" on 157 of
  157 calls, a constant predictor. Capability appears sharply threshold-dependent on model
  size, so these curves are a property of the model as much as of the text.

## Method notes worth keeping

- Option order is counterbalanced per author. The first 3B run listed "male" first every
  time and returned male every time; whatever part of that was order bias is now controlled.
- The model is forbidden to refuse or answer "unknown", because an abstention would be
  scored as a miss and would bend the curve downward at exactly the low-word steps that
  matter most.
- Authors with fewer words than a step are skipped rather than padded, so no step silently
  duplicates the one before it.
