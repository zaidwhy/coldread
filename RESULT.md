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
threshold moves by a factor of sixteen (thirty-two with the third family, below). The negative control and the second model family are what
make that a measurement rather than an anecdote.

## Caveats

- **One model, one corpus.** Everything here is `qwen2.5:7b-instruct` on 2004 blogger.com
  text. Replication on a second model family is the obvious next step, and until it exists
  these numbers describe this model rather than language models.
- ~~**Contamination is not ruled out.**~~ **Closed 2026-08-23 - see below.**
- **n = 72 authors.** The intervals are wide. Gender at 800 words clears with a lower bound
  of 0.54 against a 0.50 bar, which is a pass but a narrow one. Treat 800 as "somewhere in
  the high hundreds", not as a precise figure.
- **Demographic attributes, plus industry (step 3, 2026-10-04).** Gender and age band, and
  since step 3 industry (see the last section). Income, location and employer are still not
  tested here and must not be claimed.
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

## Third model family, same size class (run 2026-09-22, written up 2026-09-27)

The two-model result left a confound: the models differ in family and in size at once. `mistral:7b`
(a third lab, the same 7-8B class as both earlier models) ran through the identical sample, seed
(1938), temperature (0) and prompt; `sweep.py` and `build_sample.py` are unchanged since the first
run, and the 504 (author, words) cells match the other two runs exactly. 504 calls, 0 errors,
0 unparsed. Reproduce with `python analyze.py out/results-mistral_7b.jsonl`.

| words | gender | age band | sign (control) |
|---|---|---|---|
| 25 | 44.4% [0.34, 0.56] | **45.8%** [0.35, 0.57] | 13.9% [0.08, 0.24] |
| 50 | 55.6% [0.44, 0.66] | 50.0% [0.39, 0.61] | 15.3% [0.09, 0.25] |
| 100 | 55.6% [0.44, 0.66] | 56.9% [0.45, 0.68] | 16.7% [0.10, 0.27] |
| 200 | 54.2% [0.43, 0.65] | 58.3% [0.47, 0.69] | 15.3% [0.09, 0.25] |
| 400 | 59.7% [0.48, 0.70] | 63.9% [0.52, 0.74] | 15.3% [0.09, 0.25] |
| 800 | 59.7% [0.48, 0.70] | 62.5% [0.51, 0.73] | 12.5% [0.07, 0.22] |
| 1600 | **63.9%** [0.52, 0.74] | 70.8% [0.59, 0.80] | 13.9% [0.08, 0.24] |

| | qwen2.5:7b-instruct | llama3.1:8b | mistral:7b |
|---|---|---|---|
| gender half-life | 800 words | 50 words | 1600 words |
| gender at 1600 words | 72.2% | 90.3% | 63.9% |
| age band half-life | 100 words | 25 words | 25 words |
| age band at 1600 words | 58.3% | 59.7% | 70.8% |
| star sign (control) | never | never | never |

### What held

- **The control held in all three.** Star sign never cleared its bar. Mistral's point estimate
  touched 16.7% at 100 words, just above the 15.3% bar, but its lower bound was 0.10; no step in
  any model has an interval above the bar.
- **Age clears before gender in all three**, and in Mistral by the widest margin (25 words against 1600).
- **Reader-dependence is not a size effect.** With size held to one class, family alone moves the
  gender half-life from 50 to 1600 words, a thirty-two-fold spread on identical text. Size may still
  matter (the 3B model could not do the task at all), but it cannot explain a spread this wide among
  models of one size class.

### What did not hold

- **The shared age ceiling.** 58.3% and 59.7% looked like a property of the text. Mistral reaches
  70.8% [0.59, 0.80] at 1600 words and is still climbing. The intervals overlap Llama's, so this does
  not prove the ceilings differ, but "age band caps near 60% regardless of the reader" is withdrawn.
- **One ordering of readers.** Mistral is the slowest reader of gender and tied fastest on age band.
  Which model "reads better" depends on the attribute, so no single ranking of readers exists either.

### On the below-chance zone

Mistral reads 44.4% on gender at 25 words, the same point estimate as Qwen, then 55.6% at 50. Llama
never dips. As with Qwen, the interval at 25 words includes 0.50, so "worse than chance" remains
unestablished for any model; the dip is an observation in two of three families, not a finding.

### Scope

Mistral's gender pass is the narrowest in the study: it clears only at the last step, with a lower
bound of 0.52, so read its half-life as "about 1600 words or more". Still one corpus, 72 authors,
demographic attributes only, and one size class; two sizes of one new family would test size
directly.

## Two sizes of one family (run 2026-09-27, deposited as v1.2.0)

The third-family section showed that family moves the threshold at one size. This asks the other
half: inside one family, does size matter? `llama3.2` at 3.2B parameters (Q4_K_M) ran through the
identical sample, seed, temperature and prompt as `llama3.1:8b`. Reproduce with
`python analyze.py out/results-llama3.2_latest.jsonl` (add `--json` for the numbers below).

Three of the 504 calls never finished: for two authors at 400 and 800 words the model generated
until the 600-second read timeout on all five attempts. At temperature 0 that is deterministic, so
the rows are reported missing rather than retried with a different setting; those two steps have
n = 71 and n = 70, and the best constant guess moves slightly (gender 50.3%).

| words | gender | age band | sign (control) |
|---|---|---|---|
| 25 | 45.8% [0.35, 0.57] | 43.1% [0.32, 0.55] | 11.1% [0.06, 0.20] |
| 50 | 45.8% [0.35, 0.57] | 41.7% [0.31, 0.53] | 12.5% [0.07, 0.22] |
| 100 | 47.2% [0.36, 0.59] | **52.8%** [0.41, 0.64] | 6.9% [0.03, 0.15] |
| 200 | 47.2% [0.36, 0.59] | 55.6% [0.44, 0.66] | 4.2% [0.01, 0.12] |
| 400 | 46.5% [0.35, 0.58] n=71 | 54.9% [0.43, 0.66] n=71 | 5.6% [0.02, 0.14] n=71 |
| 800 | 55.7% [0.44, 0.67] n=70 | 51.4% [0.40, 0.63] n=70 | 2.9% [0.01, 0.10] n=70 |
| 1600 | 61.1% [0.50, 0.72] | 63.9% [0.52, 0.74] | 5.6% [0.02, 0.13] |

| | llama3.2 (3B) | llama3.1:8b |
|---|---|---|
| gender half-life | never (61.1% at 1600, lower bound 0.50) | 50 words |
| age band half-life | 100 words | 25 words |
| star sign (control) | never | never |

### What this shows

- **Size matters inside a family, and a lot.** The 8B model clears gender at 50 words; the 3B model
  never clears it within 1600. Together with the previous section, both reader properties move the
  threshold: family at a fixed size, and size within a family.
- **The control held again.** Star sign never cleared its bar; its highest point was 12.5% at 50 words.
- **Age still clears before gender**, now in all four readers that clear anything.

### Scope

This is one family at two sizes, and the two are also different releases (3.2 against 3.1), so
"size" here means size plus one release step. `qwen2.5:3b` could not do the task at all (a constant
predictor), which fits the same direction but is not a controlled comparison.

## Step 3: industry as a fourth attribute (run 2026-10-04, not yet deposited)

Decision and design are in `PLAN.md` (change log, written before any industry data): the corpus's
own self-reported industry, adults only (23-47), four industries (Education, Technology, Arts,
Communications-Media), 18 authors each = 72, balanced on gender and on age band inside every
industry. Same slices, temperature 0, seed 1938, star sign as the control, the four readers already
run for gender and age. The best constant guess is 25% for industry and 12.5% for sign. The live app
is not changed and no per-author output is published.

| Reader | Industry half-life (words) | Industry at 1600 words | Unparsed | Gender half-life (words) |
|---|---|---|---|---|
| llama3.1:8b | 25 | 47.2% | 0 / 504 | 50 |
| qwen2.5:7b-instruct | 50 | 41.7% | 0 / 504 | 800 |
| mistral:7b | 50 | 51.4% | 0 / 504 | 1600 |
| llama3.2 3B | 200 | 32.8% (n=61) | 27 / 504 | never |

Reproduce each row with `python analyze.py out/results-industry-<model>.jsonl` (outputs in
`out/analysis-industry-*.txt`); `tests/test_industry.py` asserts the half-lives and that the control
never clears.

### What held

- **The control is clean.** Star sign never clears its 12.5% bar at any of the seven word counts for
  any of the four readers, so the pipeline is not leaking labels. This was the pre-registered gate
  and it was checked on qwen first.
- **Industry is inferable from very little text.** All three 7-8B readers clear 25% by 50 words, and
  the llama 8B already at 25. The pre-registered rule for a headline (same direction in the qwen and
  llama families) is met.
- **Accuracy plateaus, it does not climb to certainty.** Best points are 44% (qwen, 400 words), 51%
  (mistral, 1600) and 50% (llama 8B, 400): about twice chance on a four-way choice, not a reliable
  classifier. The interval lower bounds sit near 0.3 to 0.4.

### What this does and does not show

- **Different from the gender curve.** Industry clears with far less text than gender did for qwen
  (50 against 800) and mistral (50 against 1600), and llama 8B is the earliest on both. The readers
  that were slow on gender are not slow on industry. Caution on the comparison: industry is a four-way
  choice with a 25% bar, gender a two-way choice with a 50% bar, on a different 72-author sample (adults
  only), so the half-life numbers are not on one scale. It is a contrast, not a ranking of attributes.
- **A topic shortcut is not ruled out.** An educator writing about school or a developer writing about
  code names an industry through vocabulary, with no inference about style. Nothing in this run
  separates the two routes, so the result says "an industry label is recoverable from a few dozen
  words of ordinary blog text", not "from how someone writes". Masking topic words is the obvious next
  test and was not run.
- **The 3B reader is weak and partly lost.** It clears only at 200 and 400 words (lower bounds 0.26
  and 0.25, against a 0.25 bar) and falls back below it at 800 and 1600. 27 of 504 replies were
  unparsed (it adds fields such as age and occupation), which shrinks n to 61-70 at the longer slices.
  Read its half-life as "weak and unstable", not as 200.
- **One run, one corpus, n = 72, temperature 0.** Self-reported 2004 blog labels, noisy for industry.
  No paired test between readers was run.

### Mid-run change, and a determinism correction

Qwen and mistral ran first with no output cap. The llama 3B run stalled on runaway generations (10
timeouts of 600 s in its first 103 calls), so `sweep.py --task industry` now sends `num_predict: 200`
(valid replies are under 60 tokens), the timed-out rows were re-run, and the change was logged in
`PLAN.md` before any llama result was read.

The first version of this note said replies are identical with or without the cap. That was untested and
wrong. Measured on 24 random calls each, a re-run differs from the original in 5 (qwen) and 2 (mistral)
predictions, and a re-run without the cap differs just as often, so the cause is not the cap:
Ollama at temperature 0 with a fixed seed is not fully deterministic on this machine, and isolated
predictions flip. The local "deterministic" wording elsewhere in this repo should be read as "same
settings", not "same output".

**How much it matters, measured.** The full qwen and llama 8B industry sweeps were each run a second time
(`out/replicate-industry-*.jsonl`). Llama 8B reproduced exactly: 0 of 504 predictions differ and the
half-life is 25 words again. Qwen: 25 of 504 industry predictions differ, but they
cancel almost exactly. Hit counts are identical at six of seven word counts (the seventh, 1600 words,
is 30/72 against 31/72), the half-life is 50 words in both runs and the sign control never clears in
either. So for qwen the run-to-run noise is about one point per curve (none for llama 8B), small against the 25 to 50 point
gap between industry accuracy and chance, but a half-life that sits one point above the bar (the 3B
reader) should not be trusted to the word count.
