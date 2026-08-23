# COLD READ

**The question: how many words can you write before a machine knows who you are?**

Status: Phase 0 (validation) running 2026-08-23. Nothing is built beyond the measurement
until the measurement says there is something to build.

---

## The claim being tested

Large language models can infer personal attributes from ordinary text. That much is
established. What nobody has measured is the *threshold*: the point on the input-size axis
where a reader stops being anonymous. If that threshold is low and sharp, it is a number
worth knowing and a thing worth showing people.

Working name for the quantity: **the anonymity half-life**.

## Novelty position (checked 2026-08-23, do not re-derive)

| Prior work | What it took | What it left |
|---|---|---|
| Beyond Memorization (arXiv 2310.07298) | LLMs infer location, income, sex, age from Reddit text at near-human accuracy, ~1/100 the cost | No input-size sweep. Treats inference as a capability, not a curve |
| Large-scale online deanonymization with LLMs (arXiv 2602.16800) | Linking two pseudonymous profiles to each other; 68% recall at 90% precision; "practical obscurity no longer holds" | Linkage, not attribute inference. No threshold analysis |
| Author-profiling literature (PAN, PART, etc.) | Accuracy improves with more text, stated qualitatively | Never localises where the curve leaves chance |

The gap is the curve itself, per attribute, with a control.

## Design

**Corpus.** Blog Authorship Corpus (Schler et al. 2006) via `tasksource/blog_authorship_corpus`.
19,320 bloggers, ~35 posts and 7,250 words each, self-reported gender, age, industry and star
sign. Free for non-commercial research. 9,947 authors clear the 2,000-word floor.

**Sample.** 72 authors, balanced 12 per cell across (13-17, 23-27, 33-47) x (male, female), so
neither inferable attribute can be won by guessing the majority class.

**Sweep.** Each author's own first 25, 50, 100, 200, 400, 800, 1,600 words, one call per cell,
temperature 0, fixed seed. The model must commit to gender, age band and star sign every time;
refusal and "unknown" are forbidden, because an abstention would silently become a wrong answer
and bend the curve.

**The control.** Star sign is labelled in the corpus and is not inferable from text. It is
carried through the identical pipeline as a negative control. Gender and age may climb. Sign
must not. If sign climbs, something is leaking - contamination, prompt artefact, or a bug - and
the result is void.

**Baseline.** The bar is the best constant guess computed from the sample, not 1/k. Signs are
unevenly distributed (Aquarius is 11 of 72), so always answering the commonest sign scores
15.3%, and the control has to survive that rather than the softer 8.3%.

**Statistic.** Wilson score interval at 95%. An attribute has cleared when the lower bound
exceeds the best constant guess. The half-life is the smallest word count where that happens.

## The gate, pre-registered

Set before any results were seen:

1. Gender or age band must clear the baseline somewhere in 25 to 1,600 words.
2. Star sign must not clear it at any step.

Fail 1 and there is no curve, no countdown, and COLD READ is dead.
Fail 2 and the pipeline is measuring an artefact and must be fixed before anything is believed.

Known ambiguity, stated in advance: the pilot runs on a 3B model, and the published work shows
this capability scales hard with parameter count. A flat curve on a 3B is therefore not proof of
absence. If gender comes back flat the sweep re-runs on a 7B before any verdict is given. This
is written down so the re-run cannot look like moving the goalposts afterwards.

## Caveats to carry forward

- The corpus is public and labelled, so contamination is conceivable: a model could in principle
  have memorised author-to-attribute mappings rather than inferring them. The sign control
  catches the crude version of this. A stronger check is to re-run on text the model cannot have
  seen paired with its labels.
- Self-reported labels from 2004 blogger.com. Age and gender are the reliable fields; industry
  is frequently "unknown"; sign is unverifiable, which is exactly why it makes a good control
  rather than a target.
- Attributes here are demographic. The more invasive inferences in the literature (income,
  location) are not tested and should not be claimed.

## If the gate passes: the artefact

The measurement becomes an interface rather than a chart.

**Two seats.** Two people, both opted in, hold a conversation through it. Each sees two files
filling in live: their own and the other person's. A counter drains as they type - *anonymous
for 41 more words* - which is the curve rendered as UI. You watch yourself become known while
watching someone else become known, and you cannot stop talking without it being strange.

**The rule that makes it publishable under your own name.** It only ever reads text a person
knowingly typed into it. No scraping the other party, no camera, nobody profiled who did not sit
down. The exhibit is about the harm; the moment it profiles a non-consenting third party it
becomes the harm.

## Layout

- `build_sample.py` - corpus to balanced per-author sample
- `sweep.py` - the input-size sweep, resumable, deterministic
- `analyze.py` - accuracy curves, Wilson intervals, half-life, control check
- `data/` - corpus and sample (gitignored, 763MB)
- `out/` - results as JSONL
