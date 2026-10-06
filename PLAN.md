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

## Change log

### 2026-10-04 - step 3: industry added as a fourth attribute (Zaid approved the decision in HANDOFF.md)

Written before any industry data exists. The gender and age-band design above is unchanged and its results are not re-derived.

- **Attribute:** industry, the corpus's own self-reported `topic` field. Location, employer and income stay out of scope. The two-seat live app is not extended; it still profiles nobody but consenting seats. Per-author outputs are not published.
- **Sample (`data/sample_industry.json`):** adults only (ages 23-47), four industries (Education, Technology, Arts, Communications-Media), 18 authors each = 72, balanced on gender (9/9) and on age band (23-27, 33-47; 9/9) inside each industry, at least 2,000 words each, seed 1938. Best constant guess = 25%.
- **Sweep:** same slices (25 to 1,600 words), temperature 0, seed 1938, option order counterbalanced per author. Each reply names industry and star sign (gender and age band are not asked; every author is an adult).
- **Control:** star sign, same rule as above. Best constant guess is computed from the sample.
- **Gate, before the full sweep:** on qwen2.5:7b-instruct the sign control must not clear its best constant guess at any step. If it does, the pipeline is fixed before anything is believed. Industry clearing or not is not a gate: a flat industry curve is reported as a result.
- **Half-life:** identical definition, the smallest word count whose Wilson 95% lower bound exceeds the best constant guess.
- **Readers:** qwen2.5:7b-instruct, llama3.1:8b, mistral:7b, llama3.2 3B (the four already run for gender and age), local, $0. Each is reported on its own; no pooled claim. A headline needs the same direction in both qwen and llama families, per the repo's rule.
- **Known confounds, stated in advance:** industry is self-reported and noisy; topic words in a blog can name an industry without any stylistic inference (an easier route than gender, which makes this attribute the less clean of the four); the sample is balanced on gender and age band but not on anything else.

### 2026-10-04 (later, mid-run) - output cap for the industry task

Qwen 7B and mistral 7B had finished (504 of 504, no failures). The llama3.2 3B run stalled: 10 of its first 103 calls hit the 600 s read timeout because the model never stops writing (the runaway generation already documented for this model), which would have taken many hours. Changes, made before looking at any llama result and affecting no valid reply (a valid reply is under 60 tokens):

- `sweep.py --task industry` sends `num_predict: 200` to Ollama. The default profile task is unchanged. Qwen and mistral ran before the cap existed; at temperature 0 their valid replies are the same with or without it.
- The 10 timed-out llama3.2 rows were removed and re-run under the cap. One earlier `unparsed` row (a reply with extra fields) was kept as is.
- Replies cut off by the cap, or with extra fields instead of the two asked for, are `unparsed`. As in every earlier run they are excluded from accuracy, not scored wrong, and the count is reported next to each curve. Because exclusion shrinks n, a curve with many unparsed rows is read with that n beside it.

### 2026-10-04 (correction) - the cap is not what changes replies; Ollama is not deterministic here

The entry above says qwen and mistral replies are the same with or without the cap. That was asserted, not measured, and it is wrong as stated. Measured afterwards on 24 random calls each: a re-run with the cap differs from the original in 5 of 24 (qwen) and 2 of 24 (mistral) predictions. A re-run of qwen without the cap also differs from the original in 5 of 24, and capped against uncapped re-runs differ in 4 of 24. So the cap is not the cause: at temperature 0 with a fixed seed, Ollama on this machine still flips predictions between identical runs (up to about one in five in these isolated spot checks; see the replicate result below). The "deterministic" wording in this repo's earlier text does not hold for single predictions.

Consequence and plan: the half-lives are properties of one run each. To size the noise, the qwen and llama 8B industry sweeps (the two families the headline rule needs) are re-run in full into `out/replicate-industry-*.jsonl` and the half-lives compared. Whatever that shows is reported next to the original numbers.

Result of the re-runs (full 504-call sweeps, same settings): qwen differs on 25 of 504 industry predictions and reproduces the half-life (50 words) with hit counts identical at six of seven word counts; llama 8B differs on 0 of 504 and reproduces its half-life (25 words) exactly. The sign control stays clean in both. So the flipping seen in isolated spot checks mostly does not survive a full sequential re-run, and varies by reader.

### 2026-10-06 - step 3b: topic-word masking (written before any masked run)

Question left open by step 3: does industry survive when the words that name an industry are removed, or was the result vocabulary? Design fixed here, before data:

- **Mask:** the lexicon in `topicmask.py` (four industry lists, about 150 stems, written before any masked run). ALL four lists are masked in every snippet, whatever the author's label, so masking cannot leak the label. Slices are cut first (identical to the unmasked sweep), then masked words become `[...]` and still count toward the word total. Measured before running: 1.6% of words in the first 1,600 words of the 72 authors are masked.
- **Sweep:** `sweep.py --task industry --mask-topic`, same readers' prompts, temperature 0, seed 1938, num_predict 200. Readers: llama3.1:8b and qwen2.5:7b-instruct (the two families the headline rule needs). Output `out/results-industry-masked-<model>.jsonl`. Mistral and the 3B are not re-run.
- **Control:** star sign must stay unable to clear its constant guess on both readers. If it does, nothing about masked industry is believed.
- **Decision rule (per reader, stated now):** compare the masked half-life with the unmasked one (llama 25, qwen 50 words). (a) Masked half-life no more than 2x the unmasked one and the masked plateau within 10 points of the unmasked plateau: the lexicon does not carry the signal, "industry is recoverable beyond the obvious words". (b) Masked half-life never reached within 1,600 words, or the plateau drops to the constant guess: vocabulary carries it. (c) Anything between: partial, reported as such with both curves. A headline "not just vocabulary" needs (a) in BOTH families.
- **Limits, stated in advance:** the lexicon is a coarse hand list, not exhaustive. Remaining words can still name an industry indirectly (places, products, jargon not in the list), so surviving masking shows the listed words are not required, not that no topical content is used. 2004 blog labels are self-reported and noisy. n = 72 per curve.
