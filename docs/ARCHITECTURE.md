# Architecture

System-design note for COLD READ. `README.md` tells the finding, `RESULT.md` is the record of the numbers, `PLAN.md` is the pre-registered design. This file covers how the measurement is built and why.

## Problem

Measure, per attribute, how many words a person writes before a language model can infer who they are, and show that the answer depends on which model is reading. The measurement has to be reproducible from a seeded sample build and a fixed model seed, and it needs a control that proves a rising curve is inference and not an artifact.

## Requirements

- One curve per attribute (gender, age band) with confidence intervals, from the same authors and the same words for every model.
- A negative control that cannot be inferred from writing (star sign), run through the identical pipeline.
- Replication on a second model from a different lab before any claim is a headline.
- A direct test of whether the model memorised the public corpus instead of inferring.
- Rerunning on a new model is one command and does not touch the existing results.

## Constraints

- Local models only, through Ollama: free, private, and seedable. The runs assume a laptop GPU with 4 GB of VRAM, so 7 to 9B models at 4-bit.
- The corpus is public and labelled (Blog Authorship Corpus, Schler et al. 2006), so contamination is a live objection and has its own test.
- Ethics rule: only gender and age band, both self-reported labels in the corpus. No occupation or location attributes, in the sweep or the app.
- n is 72 authors, so intervals are wide and a small difference between models is not automatically a finding.

## Architecture

```
build_sample.py      blogtext.csv -> data/sample.json (72 authors, 12 per age x gender cell, seed 1938)
        |
sweep.py             one Ollama call per (author, word count), 7 counts, 504 calls per model
        |            temperature 0, seed 1938, JSON-only reply, resumable JSONL in out/
        v
analyze.py           accuracy per attribute per word count, Wilson intervals, best-constant baseline,
        |            half-life = smallest word count whose lower bound clears the baseline
        v
RESULT.md / README   numbers copied from analyze.py output, never typed by hand

contamination_check.py   verbatim prefix -> model continues -> overlap with the true next words
                         versus a different author's next words (the gap is the signal)
server.py + index.html   two-seat consenting chat that re-profiles each seat as it types
tests/test_analysis.py   smoke test: the committed JSONL reproduces the headline numbers
```

## Data flow: one sweep

1. `sweep.py` loads `data/sample.json` and, for each author and each of 25, 50, 100, 200, 400, 800 and 1,600 words, takes that author's first N words.
2. It builds one prompt with the gender and age options listed in a deterministic per-author order, so half the authors see each option first. This exists because an early 3B run answered "male" 157 times out of 157 with "male" listed first.
3. It posts to Ollama's `/api/chat` with `temperature 0`, `seed 1938` and `format json`. The model must commit to all three attributes every time: refusal and "unknown" are forbidden, because an abstention would quietly bend the curve at the small word counts that matter most.
4. `parse_reply` takes the first JSON object in the reply. Each result, including a failed call, is appended to `out/results-<model>.jsonl` as one line.
5. `analyze.py` scores each attribute against the best constant guess (not 1 over k), attaches a 95% Wilson interval, and marks the first word count whose lower bound clears that baseline.

## Components

| Component | File | Responsibility |
|---|---|---|
| Sampler | `build_sample.py` | regroup the per-post corpus by author, balance the cells, keep star sign as the control |
| Sweep | `sweep.py` | the only place that calls a model for the study; resumable, deterministic |
| Analysis | `analyze.py` | curves, intervals, baselines, half-life; the source of every published number |
| Contamination probe | `contamination_check.py` | memorisation test with a different-author control |
| Live app | `server.py`, `index.html` | two consenting seats, one in-memory session at a time, consent gate |
| Runner | `scripts/run_model_sweep.ps1` | unattended pull, sweep, retry of failed rows, analysis, status file |
| Tests and CI | `tests/`, `.github/workflows/ci.yml` | the analysis reproduces the headline numbers from committed data |

## Failure modes

| Failure | Effect | Mitigation |
|---|---|---|
| Ollama down or model not pulled | every call raises | the exception is stored on the row, not swallowed; the runner script retries |
| Reply is not parseable JSON | no prediction for that cell | stored as an error row and counted as unparsed in the analysis header |
| A failed row on resume | `sweep.py` treats any stored row as done, so it would never retry it | the runner script removes error rows and reruns until all 504 are clean |
| Author shorter than a word count | the slice would silently duplicate the previous step | that cell is skipped, so the curve is never flattened by padding |
| Option order bias | inflated accuracy on the first-listed option | deterministic counterbalancing per author |
| The model memorised the corpus | accuracy would be retrieval | direct probe with a different-author control; run and ruled out, see `RESULT.md` for which models |

## Tradeoffs

- **Local models over API models:** free, private and seedable, but only small open models are tested. Larger or closed models are outside the claim.
- **72 authors:** balanced cells and a one-command rerun, but wide intervals, so a new model landing a few points away is not a disagreement.
- **Best constant guess as the baseline, not 1 over k:** stricter and honest about class balance, at the cost of gender's bar sitting at 50% exactly.
- **Hard-coded app thresholds:** the live app uses the measured word counts from one model, which is documented in the app and README but means it names that reader explicitly.
- **Two attributes only:** keeps the ethics bar low; extending needs an explicit written decision first.

## Scaling

1. More models: `scripts/run_model_sweep.ps1 -Model <name>` is the whole procedure, about 30 to 45 minutes per 7 to 9B model on the reference laptop.
2. More authors: raise the sample in `build_sample.py`; cost grows linearly with 7 calls per author per model.
3. Two sizes of one family, to separate size from family, which the current two models cannot do.

## Security

- No secrets and no network beyond the local Ollama endpoint. The corpus and the built sample stay under `data/`, which is gitignored; only the result JSONL files are committed.
- The live app holds one session in memory, requires consent from both seats before profiling, and stores nothing.

## Observability

Each run leaves a JSONL of every call and a log. `analyze.py` prints the record count and the unparsed count, so a partial or broken run is visible before any number is used. The runner writes a status file (`RUNNING`, `DONE`, `FAILED_PULL` or `INCOMPLETE`) next to the results.

## Cost

$0. About 4 to 5 GB of disk per model and about 30 to 45 minutes of GPU per 504-call sweep on a 4 GB laptop GPU.

## Future

- A third model family, started 2026-09-21 with `mistral:7b`; the result is not yet in `RESULT.md`.
- A second size of the new family, to test whether the qwen pattern (flat at 3B, climbing at 7B) is general.
- Any new attribute waits on a written ethics decision in `HANDOFF.md`.
