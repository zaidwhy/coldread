# COLD READ

**How many words can you write before a machine knows who you are?**

This is a measurement, not a demo. 72 authors from a public, labelled blog
corpus were shown to two local language models in increasing slices of their
own words - 25, 50, 100, 200, 400, 800, 1,600 - and the model had to commit to
a guess about the author's gender, age band, and star sign every time. Gender
and age are inferable from writing style. Star sign is not; it is the negative
control that makes the rest of this trustworthy.

## The result

`qwen2.5:7b-instruct`, temperature 0, seed 1938, 504 calls, 0 errors, 0
unparsed.

| words | gender | age band | sign (control) |
|---|---|---|---|
| 25 | 44.4% [0.34, 0.56] | 38.9% [0.28, 0.50] | 8.3% [0.04, 0.17] |
| 50 | 43.1% [0.32, 0.55] | 37.5% [0.27, 0.49] | 9.7% [0.05, 0.19] |
| 100 | 45.8% [0.35, 0.57] | **45.8%** [0.35, 0.57] | 8.3% [0.04, 0.17] |
| 200 | 51.4% [0.40, 0.63] | 52.8% [0.41, 0.64] | 5.6% [0.02, 0.13] |
| 400 | 56.9% [0.45, 0.68] | 54.2% [0.43, 0.65] | 9.7% [0.05, 0.19] |
| 800 | **65.3%** [0.54, 0.75] | 55.6% [0.44, 0.66] | 8.3% [0.04, 0.17] |
| 1600 | 72.2% [0.61, 0.81] | 58.3% [0.47, 0.69] | 8.3% [0.04, 0.17] |

Brackets are 95% Wilson score intervals, bold marks the crossing point. The
bar is the best constant guess on this sample, not 1/k: gender 50.0%, age
band 33.3%, sign 15.3% (signs are unevenly distributed, so always answering
the commonest sign already scores 15.3%).

**Half-life gender: 800 words. Half-life age band: 100 words. Sign: never.**

## What the control proves

Star sign is a labelled attribute in the corpus with no causal link to the
text. It went through the identical pipeline as gender and age band and never
left its floor - 5.6% to 9.7% across all seven steps, against a 15.3% bar. If
sign had climbed alongside the other two, it would mean the pipeline was
leaking signal from somewhere other than the writing (a prompt artifact, a
label leak, a bug), and the whole result would be void. It did not climb. That
is what makes the gender and age numbers above worth reading as inference
rather than noise.

Two other things fall out of the qwen curve. Below roughly 100 words the model
does worse than chance on gender (44.4% at 25 words, 43.1% at 50), not merely
uninformed - a short sample produces a confidently wrong guess, and the real
signal only overtakes that later. And both curves rise smoothly rather than
snapping on at a threshold: there is no clean line between "anonymous" and
"exposed," exposure accrues.

## Replication on a second model

The identical sample, prompt, seed, and battery were run again through
`llama3.1:8b` - different lab, different training corpus, comparable
parameter count. 504 calls, 0 errors, 0 unparsed.

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

- **The control held in both.** Star sign never cleared its bar at any step in
  either model. This is the load-bearing check, and it survived a second
  family.
- **Age clears earlier than gender in both**, despite the absolute numbers
  differing wildly.
- **The age ceiling is close to identical**: 58.3% and 59.7% at 1,600 words,
  from two unrelated models. Age band in this kind of text appears to cap
  near 60% regardless of the reader.

### What did not replicate

- **The below-chance zone is qwen-specific.** Qwen reads 44.4% on gender at 25
  words; llama reads 59.7% and is above chance from the first step. The claim
  that short samples produce confidently wrong guesses describes one model,
  not language models in general. Stated plainly: that finding does not
  generalize on the evidence collected so far.
- **The absolute half-life does not transfer at all.** 800 words versus 50 is
  a sixteen-fold difference on identical text.

### The finding this replaces the original headline with

**The anonymity half-life is not a property of the text. It is a property of
the reader.** Same 72 authors, same words, same prompt. One model needs 800
words to beat a coin flip on gender; another needs 50 and reaches 90.3% by
1,600. No statement of the form "you are anonymous for N words" is meaningful
without naming the model, and N falls as models improve. A third model,
`qwen2.5:3b-instruct`, was tried in the pilot and answered "male" on 157 of
157 calls - a constant predictor, not a curve. The three models line up
suggestively (3B flat, 7B anti-correlated then climbing, 8B accurate
immediately), but family and size are confounded across them, so that ladder
is a hypothesis, not a result.

## Contamination: tested and ruled out

The corpus is public and labelled, so the obvious objection is that the model
retrieved memorized authors rather than inferring anything from their writing.
This was tested directly with `contamination_check.py`: feed the model a
verbatim 50-word prefix from an author, let it generate a continuation, and
score that continuation twice - against the author's real next 50 words, and
against a different author's next 50 words. English trigram overlap is never
exactly zero, so only the gap between the two scores is informative.

`qwen2.5:7b-instruct`, 20 authors:

| | mean trigram overlap |
|---|---|
| true continuation | 0.0021 |
| control continuation | 0.0000 |
| **gap** | **+0.0021** |

Effectively nothing. Two of twenty authors produced a single matching
trigram; the other eighteen produced none.

The probe itself was checked, not assumed, because a null result from a
broken instrument proves nothing. The model generates 99 words of fluent,
on-topic continuation - it is genuinely attempting the task, not stalling.
Given a prefix about a Nebraska rock band it invents plausible album tracks
("A New Beginning," "I Am Not A Machine") where the real author actually
wrote "in almost a Punk Metal genre... or maybe Alternative Emo? Lol." Fluent,
confident, and nothing like the source - that is what a model that has never
seen the text looks like.

A second argument from the main result points the same way: retrieval does
not slope. A model looking up memorized authors would spike once enough text
triggered a match. What the curves actually do is climb smoothly from below
chance at 25 words. Gradual improvement from an anti-correlated start is the
signature of inference, not lookup.

Scope of the claim: this rules out verbatim memorization of this corpus by
this model. It does not prove no model has ever memorized it.

## The artifact

A two-seat chat app. Two people, both consenting, talk through it. After every
message, the seat that sent it gets re-profiled from everything they have
typed so far, and both seats watch both profiles fill in live.

![Two-seat COLD READ session, seat A at 131 words with age band inferred and gender still unreliable, seat B at 32 words showing the red below-chance warning](docs/screenshot.png)

This is a real session against the current code, not a mockup. Seat A (left,
"You") has sent 131 words - past the age band threshold, so age band shows an
`INFERABLE` tag and a real guess (`33-47`, correct for the character written).
Gender is still short of its own threshold and carries an `UNRELIABLE` tag.
Seat B (right, "Them") has sent 32 words, under the 100-word floor, so the
panel shows the red warning box: at this word count `qwen2.5:7b-instruct`
scores worse than a coin flip on gender, which the interface names explicitly
rather than presenting a low-confidence-looking guess as neutral. Star sign is
always shown and always marked `control - never inferable`, because it is the
same negative control from the sweep, running live.

The thresholds in the app (100 words for age band, 800 for gender) are the
measured `qwen2.5:7b-instruct` numbers above, not chosen for effect. They are
specific to that model, and the app names the model in the warning box for the
same reason the "what did not replicate" section above exists: a threshold
without a named reader is not a fact, it is a slogan.

## How to reproduce

Requires a local Ollama with the target models pulled, and the corpus
downloaded separately (see below).

```
# 1. Build the balanced 72-author sample from the raw corpus
python build_sample.py

# 2. Run the sweep for a given model (resumable, appends to out/)
python sweep.py --model qwen2.5:7b-instruct
python sweep.py --model llama3.1:8b

# 3. Turn results into the accuracy tables and half-life numbers
python analyze.py out/results-qwen2.5_7b-instruct.jsonl
python analyze.py out/results-llama3.1_8b.jsonl

# 4. Check for corpus memorization
python contamination_check.py --model qwen2.5:7b-instruct

# 5. Run the two-seat app
python server.py
# open http://127.0.0.1:8420/?seat=a and ?seat=b in two windows
```

The corpus itself (`data/blogtext.csv`, ~763MB) is gitignored and not part of
this repository. It is the Blog Authorship Corpus (Schler et al. 2006),
available as `tasksource/blog_authorship_corpus` on Hugging Face, free for
non-commercial research.

## Caveats

- **n = 72 authors.** The intervals are wide. Gender at 800 words clears with
  a lower bound of 0.54 against a 0.50 bar on qwen - a pass, but a narrow one.
  Treat 800 as "somewhere in the high hundreds," not as a precise figure.
- **Two models.** `qwen2.5:7b-instruct` and `llama3.1:8b`. A third model,
  `qwen2.5:3b-instruct`, was a constant predictor and produced no curve at
  all, so capability here is size-dependent as well as family-dependent, and
  family and size are confounded across the three models actually run.
- **Demographic attributes only.** Gender and age band. The more invasive
  inferences reported elsewhere in the literature - income, location,
  employer - are not tested here and are not claimed here.
- **One corpus.** 2004 blogger.com text. Self-reported labels; age and gender
  are the reliable fields.

## The ethics rule

The app reads only text a person knowingly typed into it, on that screen, in
that session. No scraping the other party, no camera, nobody profiled who did
not sit down and consent. Profiling does not start until both seats have
agreed. Nothing is saved once the server stops. The moment this tool profiles
a non-consenting third party, it stops being an exhibit about the harm and
becomes the harm - so it does not do that, structurally, not just by policy.

## Prior work

- **Beyond Memorization** (arXiv 2310.07298) established that LLMs can infer
  personal attributes - location, income, sex, age - from ordinary text like
  Reddit posts, at close to human accuracy and roughly 1/100 the cost. It
  treats inference as a capability. It does not sweep input size and does not
  report a threshold.
- **Large-scale online deanonymization with LLMs** (arXiv 2602.16800)
  established that LLMs can link two pseudonymous profiles to each other - 68%
  recall at 90% precision - and argues practical obscurity no longer holds.
  This measures profile linkage, not attribute inference from a single sample,
  and again reports no threshold curve.

Neither paper measures the point on the input-size axis where a reader stops
being anonymous. That gap is what this project measures, with a negative
control and a second model to check the number is not an artifact of one
reader.
