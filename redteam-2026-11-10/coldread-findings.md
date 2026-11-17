# Red-team findings: zaidwhy/coldread

Clone: fresh `gh repo clone zaidwhy/coldread`, master at `32a08e5` (38 commits). Only the public repo was read.
No model was called. Everything below is from the committed `out/*.jsonl` rows, the code, and git history.
My scripts (independent of `analyze.py`): `scratchpad/redteam/scripts/recompute.py`, `attack.py`, `attack2.py`, `attack3.py`,
each run as `python -I scripts/<name>.py coldread`.

Legend: VERIFIED = I ran it and quote the output. INFERENCE = my reading of verified numbers.

## Verdict table (ranked by severity)

| # | Claim | Verdict | One-line reason |
|---|---|---|---|
| 1 | "The line moved by a factor of thirty-two ... The only thing that changed was who was reading" (gender half-life 50 / 800 / 1600) | BROKEN as a magnitude; numbers recompute | The gap is an option-order artifact: when "female" is listed first, 3 of 4 readers answer "female" for nearly every author at every length. With "male" listed first the three 7-8B readers are 34, 34, 32 of 38 at 1600 words. |
| 2 | "Option order is counterbalanced ... whatever part of that was order bias is now controlled" | BROKEN | Split is 38/34 and unbalanced against gender (truth is the first-listed option for 30 of 72 authors); the bias is not removed, it is averaged in. |
| 3 | Below-chance dip: "stereotype matching"; the app's "scores worse than a coin flip on gender (44%) ... confidently wrong"; "retrieval does not slope ... from below chance" | BROKEN | The 44.4% is what a first-option picker scores on this sample (30/72 = 41.7%); qwen picks the first-listed gender 66 of 72 times at 25 words. The app still ships the claim the README withdrew. |
| 4 | "Why you can believe any of this: the star sign ... a prompt artifact, a label leak, a bug" | WEAKENED | Control never clears (verified in all 12 files), but it was blind to the prompt artifact that is actually present (#1-#3). |
| 5 | "the order held across all three models: age clears before gender in every one" | WEAKENED | llama3.1:8b age at 25 words is 32/72, lower bound 0.3354 vs bar 0.3333 (one hit), and fails again at 50 words; sustained crossing is 100 words, after gender (50). |
| 6 | Step 3b: "case (a) for both readers ... listed industry words are not what carries the signal" | WEAKENED | qwen masked half-life 100 rests on one hit (26/72); both masked curves drop back under the bar at 200 words; sustained crossing is 400 for both (8x and 16x, not 2x). |
| 7 | "Every commit here is signed ... and shows as Verified on GitHub" | BROKEN | 8 of 38 commits are unsigned, including the one holding the original gate and the qwen data. |
| 8 | Industry "clears chance within 25 to 200 words for all four readers" | WEAKENED | Holds for the three 7-8B readers; the 3B reader clears only because 27 unparsed replies are dropped from the denominator. |
| 9 | "The gate, pre-registered. Set before any results were seen" (PLAN.md) | UNTESTED (not verifiable) | PLAN.md and the first results file arrive in the same first commit. |
| 10 | "The obvious objection, tested" / "Contamination: tested and ruled out" | UNTESTED numbers; WEAKENED scope | No raw output committed; qwen only; the 20 probed authors are all aged 13-17; verbatim-continuation only. |
| 11 | "A 3B model answered the same way on every single call" / "157 of 157" / "could not do the task at all" | WEAKENED | Committed file has 178 of 178 "male" on 26 authors, all with "male" listed first, never re-run with the counterbalanced prompt. |
| 12 | Size inside a family: llama3.2 3B never clears gender, 8B at 50 | SURVIVED (with the #1 caveat) | Recomputes; paired McNemar p <= 0.002 from 50 words on. |
| 13 | Reader-dependence in the weak form: "N cannot be stated without naming the model" | SURVIVED in weak form | llama3.1:8b beats qwen and mistral on the same authors (paired tests); qwen vs mistral is not separable. |
| 14 | All RESULT.md tables regenerate from committed rows; test suite | SURVIVED | Every cell recomputed independently; `pytest -q` = 30 passed. |
| 15 | Industry inferable for the three 7-8B readers; replicate numbers; 1.6% masked | SURVIVED | No position confound in the industry sample; replicate diffs (25 and 0 of 504) and 1.6% reproduce. |

---

## 1. The 32x (BROKEN as a magnitude; the table numbers themselves recompute)

Claim (README.md "The mental model that turns out to be wrong"; RESULT.md lines 200-217): gender half-life 50 (llama3.1:8b),
800 (qwen2.5:7b), 1600 (mistral:7b); "Same authors. Same words. Same question ... The only thing that changed was who was reading."

a. Recompute, VERIFIED. `python -I scripts/recompute.py coldread`:

```
results-llama3.1_8b   gender HL 50   | 25:43/72 lo0.4818 50:49/72 lo0.5661* ... 1600:65/72 lo0.8126*
results-qwen2.5_7b    gender HL 800  | ... 400:41/72 lo0.4544 800:47/72 lo0.5376* 1600:52/72 lo0.6095*
results-mistral_7b    gender HL 1600 | ... 800:43/72 lo0.4818 1600:46/72 lo0.5235*
```

c. Confound, VERIFIED. `sweep.py::option_order` reverses the option list when `sum(ord(c) for c in author_id) % 2 == 1`.
That puts "male" first for 38 authors (16 male, 22 female) and "female" first for 34 authors (20 male, 14 female).
Gender hits split by which option was listed first (`python -I scripts/attack3.py coldread`):

```
male listed first (38 authors)            female listed first (34 authors)
words  qwen llama8 mistral llama3b        qwen llama8 mistral llama3b
  25    17    23     17      19            15    20     15      14
 100    18    26     26      20            15    25     14      14
 400    27    29     29      19            14    27     14      14
 800    31    31     29      24            16    29     14      15
1600    34    34     32      29            18    31     14      15
```

Confusion when "female" is listed first, 1600 words, [truth,pred] counts:

```
qwen     {(f,f):14, (m,f):16, (m,m):4}     30 of 34 answered "female"
mistral  {(f,f):14, (m,f):20}              34 of 34 answered "female" (same at 100, 200, 400, 800)
llama3b  {(f,f):14, (m,f):19, (m,m):1}     33 of 34 answered "female"
llama8   {(f,f):13, (f,m):1, (m,f):2, (m,m):18}
```

Fisher exact, male-first vs female-first accuracy at 1600 words: qwen p=0.0007, mistral p=0.0002, llama3b p=0.0076, llama8 p=1.0.

So for 34 of the 72 authors, qwen, mistral and llama3.2 return the first-listed option regardless of 1600 words of text.
The pooled "half-life" of 800 and 1600 is the length at which the male-first half alone drags the pooled mean over 0.50.
In the male-first half the three 7-8B readers are indistinguishable at 800 and 1600 words (31/31/29 and 34/34/32 of 38).
Half-lives inside the male-first half, same Wilson rule: bar 0.50 gives llama8 100, mistral 100, qwen 400 (4x);
bar = best constant guess in that half (22/38 = 0.579) gives llama8 200, mistral 400, qwen 800 (4x). Not 32x, and mistral is not the slowest.

INFERENCE and its limit: the two halves are different authors (n = 38 and 34), not the same authors under both orders, so the
order effect is confounded with author subset. Against that: the split is by id parity (arbitrary), and llama8 scores the same
on both subsets (34/38 and 31/34), so the subsets are not intrinsically easier or harder. A direct test (every author under both
orders) is not in the repo.

c2. Sampling stability, VERIFIED. Author bootstrap, B = 5000, same rule (`attack.py`):

```
some reader never clears: 1726 (34.5%) | ratio 16: 1188 | ratio 32: 1080 (21.6%) | ratio 8: 500 | ratio 64: 393 | ratio 4: 93 | ratio 2: 19
```

The README's "between 16x and 64x" is grid resolution only; it is not a sampling interval. Mistral's crossing is 2 hits wide
(disclosed), qwen vs mistral differ at no step in a paired test (McNemar p from 0.035 uncorrected, in mistral's favour at 50 words,
to 1.0), and each gender sweep is a single run on a stack the repo itself measured as non-deterministic
(qwen replicate: 60 of 504 rows differ in some field, VERIFIED).

Smallest honest rewording: "On identical text and one prompt, llama3.1:8b is more accurate on gender than qwen2.5:7b and
mistral:7b at every length from 100 words (paired p <= 0.02 each, uncorrected). The pooled first-crossing lengths are 50, 800 and
1600 words, but that spread is produced mostly by option order: qwen and mistral answer 'female' almost always when it is listed
first. With 'male' listed first all three reach 84 to 89 percent at 1600 words and the crossing lengths differ by about 4x.
The ratio is not estimated; a bootstrap puts 32x in 22 percent of resamples."

## 2. "Option order is counterbalanced ... now controlled" (BROKEN)

RESULT.md line 88-89; docs/ARCHITECTURE.md line 71 ("Option order bias | inflated accuracy on the first-listed option | deterministic counterbalancing").

VERIFIED (`attack.py`, `attack2.py`):

```
flip count 34 of 72
flip x gender: (maleFirst,female) 22, (maleFirst,male) 16, (femFirst,female) 14, (femFirst,male) 20
truth is first-listed gender for 30 of 72 authors
qwen    25 words: first-listed chosen 66/72     llama3b 25 words: 65/72     mistral 25 words: 55/72     llama8: 37/72
```

Counterbalancing by id parity was not stratified inside the gender cells, so a pure first-option picker scores 41.7%, not 50%.
More important, counterbalancing does not control an order effect, it mixes a working condition with a dead one (#1).
Order-balanced accuracy (four truth x order cells weighted equally) at 25 words: qwen 0.515, mistral 0.494, llama3b 0.526.

Smallest honest rewording: "Option order alternates by author-id parity (38 male-first, 34 female-first, not balanced within
gender). Three of four readers are strongly order-sensitive; results are reported per order."

## 3. The below-chance dip (BROKEN where it is still asserted)

- RESULT.md lines 43-48 (kept "as originally written"): "short samples ... produce confident anti-correlated guesses ... stereotype matching".
- README "The obvious objection": "These curves climb smoothly, in one case from below chance. Gradual improvement from an anti-correlated start is the signature of inference, not lookup."
- `index.html` line 348-349: "below 100 words, <model> scores worse than a coin flip on gender (44%). These are confidently wrong"; `server.py` line 155-157 sets `below_chance = word_count < 100`. README "The artifact" presents this as a virtue.

VERIFIED: qwen at 25 words is 32/72 with first-listed chosen 66/72; a first-option picker scores 30/72. Mistral 32/72 with first-listed 55/72.
Exact one-sided binomial for "below 0.5" is not significant in any model (README already says so). Order-balanced it is 0.515.

INFERENCE: the dip is the counterbalancing imbalance times position bias, not stereotype matching and not anti-correlation.
The app states as measured fact a claim the README says is "an observation, not a finding", and the contamination argument leans on it.

Smallest honest rewording: delete "worse than a coin flip" from the app and the "anti-correlated start" sentence; say
"at short lengths qwen returns the first-listed option about 9 times in 10".

## 4. The star-sign control (recomputes; WEAKENED as evidence)

VERIFIED: sign never clears in any of the 12 result files (max lower bound 0.098, mistral 100 words, bar 0.1528). The control is in the same tables as the headline.

What it could not catch, VERIFIED: readers answer sign with a near-constant token (llama3.1:8b industry run "gemini" 409 of 504;
qwen industry "libra" 303 of 504; llama3.2 profile "scorpio" 250 of 501), and that token is not the first-listed sign, so a
position artifact on the two-way and three-way fields is invisible to it. The README says a clean control rules out "a prompt
artifact, a label leak, a bug in the scoring"; a prompt artifact is present (#1) and the control stayed clean.

Smallest honest rewording: "The control rules out a label leak and a scoring bug that would lift every attribute. It does not
test for option-order or default-answer artifacts on gender and age."

Not checkable from the repo: "6 of 72 authors mention star-sign or birthday terms" (text is not committed).

## 5. "Age clears before gender in every one" (WEAKENED)

VERIFIED:

```
llama3.1:8b age_band: 25:32/72 lo0.3354*  50:29/72 lo0.2972  100:36/72 lo0.3875* ...   bar 0.3333
llama8 age_band HL 25, sustained HL 100 | -1 hit -> 100        llama8 gender HL 50 (sustained 50)
bootstrap: llama8 age before gender in 1877 of 5000 resamples (37.5%); all three readers in 1790 (35.8%)
```

One hit fewer at 25 words (31/72, lb 0.3226) and llama's age half-life is 100, after gender. The cell also un-clears at 50 words,
so the "first crossing" rule is rewarding a single noisy cell. "The slowest reader of gender is tied fastest on age" depends on the same cell.
Paired tests find no reader difference on age band at any step (all McNemar p >= 0.052 uncorrected).

Smallest honest rewording: "Age clears before gender for qwen and mistral. For llama3.1:8b the two are not separable: age clears
at 25 words by one author, fails at 50, and holds from 100; gender holds from 50."

## 6. Step 3b masking, "case (a) in both families" (WEAKENED)

RESULT.md line 367; CHANGELOG line 17. VERIFIED:

```
masked qwen   : 25:19 50:25/72 lo0.2475  100:26/72 lo0.2598*  200:24/72 lo0.2353  400:28* 800:28* 1600:27*
masked llama8 : 25:23 50:29/72 lo0.2972* 100:29*              200:24/72 lo0.2353  400:36* 800:34* 1600:34*
industry qwen_m  HL 100, sustained 400 | -1 hit -> 400
industry llama8_m HL 50, sustained 400
mask paired, 200 words: qwen unmasked-only-hit 8, masked-only-hit 2; llama8 unmasked-only-hit 8, masked-only-hit 2
```

The pre-registered rule keys on first crossing, and by that letter the verdict is (a). But qwen's "100" is one hit above the bar
(25/72 would make it 400, an 8x shift, case (c)), and both masked curves fall back under the bar at 200 words. With a
"clears and stays cleared" reading the shifts are 50 -> 400 and 25 -> 400. Pooled over the two readers at 200 words masking loses
16 hits and gains 4 (sign test p = 0.012; this step was picked after looking, one of seven). The README wording is already softer
than RESULT.md; RESULT.md still says the rule's condition is met "for the claim that the listed industry words are not what carries the signal".

Smallest honest rewording: "Masking 1.6% of words leaves accuracy at 400 to 1600 words unchanged for llama (36, 34, 34 of 72 both ways)
and 3 to 4 hits lower for qwen. Below 400 words both masked curves are unstable around the bar; the first-crossing rule returns (a),
but qwen's result is one hit from (c)."

## 7. "Every commit here is signed" (BROKEN)

README last section; `.zenodo.json` notes. VERIFIED:

```
git log --format='%G?' | sort | uniq -c      ->  30 G, 8 N
N ca2a2ec 2026-08-23 COLD READ phase 0: measure the anonymity half-life
N 3dad627, 0a7316e, 2563fe4, a89ae54, 707e2d0, 6d0eff6, 6c2bdf5
gh api repos/zaidwhy/coldread/commits/ca2a2ec --jq .commit.verification  -> {"reason":"unsigned","verified":false}
gh api repos/zaidwhy/coldread/commits/32a08e5 ...                         -> {"reason":"valid","verified":true}
```

The unsigned eight are the ones that carry the qwen data, the gate, the contamination result and the llama replication.
Smallest honest rewording: "Commits from 2026-09-04 onward are signed; the first eight (23-24 Aug 2026) are not."
Also minor: the plate alt text says 37 commits; `git rev-list --count HEAD` is 38.

## 8. Industry "for all four readers" (WEAKENED)

README "What this is not"; commit 307df25 subject. VERIFIED:

```
3B 200 hits 25 parsed 70 lo(excl) 0.2550  lo(unparsed = miss) 0.2475
3B 400 hits 23 parsed 64 lo(excl) 0.2529  lo(unparsed = miss) 0.2233
industry llama3b HL(excl unparsed) 200, HL(unparsed = miss) None
3B unparsed by truth: Education 11, Communications-Media 9, Technology 4, Arts 3
```

RESULT.md "Method notes" says an abstention "would be scored as a miss"; `analyze.py` drops rows with no `pred` from the
denominator. The exclusion rule for this run was written into PLAN.md mid-run (after 103 of the 3B calls), and unparsed rows are
not label-neutral. RESULT.md already calls the 3B "weak and unstable"; the README sentence does not.

For the three 7-8B readers the result holds up, VERIFIED: no order confound in this sample (truth is first-listed for 19 of 72;
expected hits from the readers' position or label marginals alone are 17.4 to 18.2, observed 26 to 37 from 50 words), and the
replicates reproduce (llama 0 of 504 differ; qwen 25 of 504 industry predictions differ, half-life 50 again).
Limits the prose understates, VERIFIED: llama's "25 words" is one hit (26/72, lb 0.2598; 25/72 gives 50); Technology is recovered
for 3 of 18 authors at 1600 words by all three readers (below the 4.5 expected by chance), so "industry" here is mostly
Arts and Communications-Media.

Smallest honest rewording: "Industry clears a 25% bar by 50 words for the three 7-8B readers (llama at 25 by one author). The 3B
reader does not clear once its 27 unparsed replies are counted as misses."

## 9. Pre-registration (original gate UNTESTED; steps 3 and 3b supported by commit order only)

VERIFIED: `git log -- PLAN.md` and `git log -- out/results-qwen2.5_7b-instruct.jsonl` both start at `ca2a2ec` (2026-08-23 13:49).
The gate "set before any results were seen" and the results it gates are one commit, so the order cannot be checked. PLAN.md itself
says a 3B pilot had already run, and the archived pilot file is in the same commit.
Step 3: design `43a7846` 11:10, results `307df25` 15:00 the same day; PLAN.md was edited again inside the results commit (the output
cap and unparsed-exclusion entries, disclosed). Step 3b: lexicon and rule `2be814f` 18:35, results `90a72d3` 19:12; `topicmask.py`
has no later commit. Commit times are author-set, so this is consistent with pre-registration, not proof of it.

## 10. Contamination (numbers UNTESTED; scope WEAKENED)

README "The obvious objection, tested"; RESULT.md lines 96-129.
- No output of `contamination_check.py` is committed, so 0.0021 / 0.0000 and "two of twenty" cannot be recomputed. Running it fails
  at `data/sample.json` (not in the repo) before any model call.
- VERIFIED from code and row order: it takes `authors[:20]` of the sample, which is ordered by cell. The first 20 authors are
  12 male and 8 female, all aged 13-17. No adult author was probed.
- Run on qwen only (RESULT.md line 105). The reader with the strongest result, llama3.1:8b (90.3%), and mistral were not probed;
  the README says "the model" without naming it.
- It tests verbatim continuation of a 50-word prefix. It does not test whether a model associates an author's text with labels,
  and the hard-coded verdict threshold (gap > 0.05) is not justified anywhere.
- The second argument ("from below chance ... signature of inference") rests on #3.
RESULT.md's own scope line ("verbatim memorisation of this corpus by this model") is accurate; the README heading and HANDOFF ("ruled out") are stronger than it.

Smallest honest rewording: "A verbatim-continuation probe on qwen2.5:7b, 20 teenage authors, found no memorised continuations.
Not run on llama3.1:8b or mistral; raw output not archived."

## 11. qwen 3B "constant predictor" (WEAKENED)

VERIFIED: `out/archive/results-qwen2.5_3b-instruct-PREBALANCE.jsonl` has 178 rows, 26 authors, 178 of 178 predictions "male";
RESULT.md, `sweep.py` and ARCHITECTURE.md say 157 of 157. The run predates option-order alternation ("male" always first) and
no counterbalanced 3B qwen run is in the repo. Given #1 (qwen 7B itself answers the first-listed option 33 of 38 and 33 of 34 times
at 25 words), "could not do the task at all" is not separable from "picks the first option". HANDOFF line 82 and ARCHITECTURE line 104
still build on "flat at 3B, climbing at 7B".

## 12-15. What survived

- Every table in RESULT.md recomputes from the rows with my own code (all half-lives, hit counts, bars 0.50 / 0.333 / 0.1528 / 0.25 / 0.125,
  sample balance 36/36, 24/24/24, 18 x 4). `analyze.py` output matches 9 of 10 committed `out/analysis-*.txt` byte for byte; the mistral
  file differs only by a leading BOM.
- `python -m pytest -q` -> `30 passed in 4.22s` (CHANGELOG says 28; the tests assert the committed numbers, so they guard against edits,
  not against the method).
- llama3.1:8b vs llama3.2 3B on gender: McNemar (23,2) p < 0.001 at 1600 words, p <= 0.002 from 50 words. Three 3B rows missing as disclosed.
- llama3.1:8b vs qwen and vs mistral on gender: paired p <= 0.02 at 100 to 1600 words (seven uncorrected steps; with a Bonferroni factor of 7,
  five steps survive against qwen and three against mistral). This is the part of "reader matters" that stands.
- Replicate claims: qwen 25 of 504 industry predictions differ, hit counts equal at six of seven steps (30 vs 31 at 1600); llama 0 of 504.
- Masked fraction: 1852 of 115,200 words = 1.61%.

## What I could not check and why

- Any model call. `data/` is gitignored and the corpus is not redistributed, so `build_sample.py` stops at
  "missing data/blogtext.csv - download it first" (the README names a Hugging Face dataset but gives no command that produces that CSV),
  and `sweep.py` / `contamination_check.py` stop at the missing `data/sample.json`. I did not download the corpus or start Ollama.
- The direct test of finding #1: the same authors under both option orders. It needs the text and the models.
- The author texts themselves: explicit self-disclosure ("I am a 15 year old girl"), the "6 of 72 mention star-sign terms" count,
  whether slices are really each author's first N words, and what the lexicon leaves unmasked.
- That the 72 authors are the seed-1938 draw of `build_sample.py` (only ids and labels are in the rows).
- The contamination numbers and the "Nebraska rock band" example (no raw output committed).
- The spot-check counts for non-determinism (5 of 24, 2 of 24) and the 10 removed-and-re-run llama3.2 rows (not in the repo).
- Whether data existed before the "pre-registration" commits; commit timestamps are author-controlled.
- The Zenodo deposit text and DOIs, the live app (`server.py`, `verify_run.py` need Ollama), the SVG plates beyond their alt text,
  and whether CI is green on GitHub.
- Hosted-reader path (`--provider openrouter`): needs a paid key; only its offline tests ran.
