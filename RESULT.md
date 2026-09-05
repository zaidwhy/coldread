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

## Where this sits against prior work

- **The task is old.** Argamon, Koppel, Pennebaker and Schler (CACM, 2009) profiled age and gender
  from this same blog corpus by statistical means.
- **The length axis is old too.** Eder (Digital Scholarship in the Humanities, 2015) showed
  authorship attribution degrades with sample length and collapses below a minimum. That work
  sweeps length against one fixed method.
- **The LLM capability is established.** Staab et al. (arXiv:2310.07298) measured attribute
  inference by LLMs at near-human accuracy; Lermen et al. (arXiv:2602.16800) demonstrated
  large-scale profile linkage. Neither sweeps input size.

What is measured here is the interaction the older length work holds fixed and the newer capability
work does not sweep: the same 72 authors and the same slices read by two different models, where the
threshold moves by a factor of sixteen. The negative control and the second model family are what
make that a measurement rather than an anecdote.

## Caveats

- **One model, one corpus.** Everything here is `qwen2.5:7b-instruct` on 2004 blogger.com
  text. Replication on a second model family is the obvious next step, and until it exists
  these numbers describe this model rather than language models.
- ~~**Contamination is not ruled out.**~~ **Closed 2026-08-23 - see below.**
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

## Contamination: tested and ruled out

The corpus is public and labelled, so the obvious objection is that the model retrieved
memorised authors rather than inferring anything. Tested directly with
`contamination_check.py`: feed the model a verbatim 50-word prefix from an author, let it
continue, and score the continuation twice - against that author's real next 50 words, and
against a different author's next 50 words. Trigram overlap in English is never zero, so only
the gap between the two is informative.

`qwen2.5:7b-instruct`, 20 authors:

| | mean trigram overlap |
|---|---|
| true continuation | 0.0021 |
| control continuation | 0.0000 |
| **gap** | **+0.0021** |

Effectively nothing. Two of twenty authors produced a single matching trigram; the other
eighteen produced none.

The probe itself was verified rather than assumed, because a null result from a broken
instrument is worthless. The model generates 99 words of fluent, on-topic continuation - it
is genuinely attempting the task. Given a prefix about a Nebraska rock band it invents plausible
album tracks ("A New Beginning", "I Am Not A Machine") where the real author wrote "in almost a
Punk Metal genre... or maybe Alternative Emo? Lol". Fluent, confident, and nothing like the
source. That is what a model that has never seen the text looks like.

**A second argument from the main result points the same way: retrieval does not slope.** A
model looking up memorised authors would spike once enough text triggered the match. What the
curves actually do is climb smoothly from *below chance* at 25 words. Gradual improvement from
an anti-correlated start is the signature of inference, not lookup.

Scope of the claim: this rules out verbatim memorisation of this corpus by this model. It does
not prove no model has ever memorised it.

## Replication on a second model family (2026-08-23)

Identical sample, prompt, seed and battery, run through `llama3.1:8b` - different lab,
different corpus, comparable size. 504 calls, 0 errors, 0 unparsed.

| words | gender | age band | sign (control) |
|---|---|---|---|
| 25 | 59.7% [0.48, 0.70] | **44.4%** [0.34, 0.56] | 6.9% |
| 50 | **68.1%** [0.57, 0.78] | 40.3% [0.30, 0.52] | 1.4% |
| 100 | 70.8% [0.59, 0.80] | 50.0% [0.39, 0.61] | 4.2% |
| 200 | 75.0% [0.64, 0.84] | 45.8% [0.35, 0.57] | 2.8% |
| 400 | 77.8% [0.67, 0.86] | 50.0% [0.39, 0.61] | 6.9% |
| 800 | 83.3% [0.73, 0.90] | 51.4% [0.40, 0.63] | 8.3% |
| 1600 | 90.3% [0.81, 0.95] | 59.7% [0.48, 0.70] | 8.3% |

| | qwen2.5:7b-instruct | llama3.1:8b |
|---|---|---|
| gender half-life | 800 words | **50 words** |
| gender at 1600 words | 72.2% | 90.3% |
| age band half-life | 100 words | 25 words |
| age band at 1600 words | 58.3% | 59.7% |
| star sign (control) | never | never |

### What replicated

- **The control held in both.** Star sign never cleared its bar at any step in either model.
  This is the load-bearing check and it survived a second family.
- **Age clears earlier than gender in both**, despite the absolute numbers differing wildly.
- **The age ceiling is close to identical**: 58.3% and 59.7% at 1600 words, from two unrelated
  models. Age band in blog text appears to cap near 60% regardless of the reader.

### What did not replicate

- **The below-chance zone is Qwen-specific.** Qwen reads 44.4% on gender at 25 words; Llama
  reads 59.7% and is above chance from the first step. The claim in "Three findings" above that
  short samples produce confidently wrong guesses describes one model, not language models.
  It is retained above as originally written, and corrected here.
- **The absolute half-life does not transfer at all.** 800 words versus 50 is a sixteen-fold
  difference on identical text.

### The finding this replaces the original headline with

**The anonymity half-life is not a property of the text. It is a property of the reader.**

Same 72 authors, same words, same prompt. One model needs 800 words to beat a coin flip on
gender; another needs 50 and reaches 90.3% by 1600. No statement of the form "you are anonymous
for N words" is meaningful without naming the model, and N falls as models improve. The three
models run so far line up suggestively - `qwen2.5:3b` is a constant predictor, `qwen2.5:7b`
starts anti-correlated and climbs, `llama3.1:8b` is accurate immediately - but family and size
are confounded across them, so that ladder is a hypothesis and not a result.
