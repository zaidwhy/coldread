# HANDOFF

## Current state

The measurement phase is complete and closed. Gate passed on the first model
(`qwen2.5:7b-instruct`), replicated on a second (`llama3.1:8b`), and
contamination was tested directly and ruled out. RESULT.md is the record of
that and should not be re-derived or re-litigated without new evidence.

Public-facing documentation is now written:

- `README.md` - the project's public face. Both result tables, the
  side-by-side model comparison, what did and did not replicate, the
  contamination check, the two-seat app with a live screenshot, reproduce
  steps, caveats, the ethics rule, and prior work. Every number in it was
  checked against a fresh run of `analyze.py` on the actual `out/` files, not
  copied from memory of RESULT.md.
- `docs/screenshot.png` - a real session against the current server and
  index.html code (2026-08-23), not the stale root-level PNGs. Seat A at 131
  words (age band inferred, gender still unreliable), seat B at 32 words
  (red below-chance warning naming `qwen2.5:7b-instruct`). The old
  `coldread-consent.png` and `coldread-live.png` at repo root are outdated UI
  copy and remain gitignored (`*.png`); only `docs/screenshot.png` is tracked
  via a `.gitignore` exception line.

Verification actually run this session:

```
python analyze.py out/results-qwen2.5_7b-instruct.jsonl
python analyze.py out/results-llama3.1_8b.jsonl
```

Both outputs matched every number written into README.md and RESULT.md
exactly (504 records, 0 errors, 0 unparsed on each; same accuracy figures,
same Wilson intervals, same half-lives: gender 800/50, age band 100/25, sign
never/never).

Work is committed locally. **It has not been pushed to any remote** - the
repo is local-only. Whether and where to publish this (a public repo, a blog
post pointing at the README, anything else) is Zaid's call, not something to
be decided or executed by an agent.

## What is deliberately not done

- No push to any remote, per the task instructions for this session.
- No new experiments and no changed conclusions - this session only wrote
  documentation and one screenshot around results that already existed.
- No attempt to control the size/family confound across the three models
  that have been run (`qwen2.5:3b-instruct`, `qwen2.5:7b-instruct`,
  `llama3.1:8b`). The README says plainly that the "capability ladder" across
  those three is a hypothesis, not a result, because size and family both
  vary at once.
- No third model family run.
- No extension beyond the two demographic attributes (gender, age band).
  Sign is the control, not a target; occupation and location are not tested
  and must not be claimed anywhere in this repo's public copy.

## Exact next steps, if anyone resumes this

1. **Control the size/family confound.** Run a same-size, different-family
   model against the identical sample/prompt/seed/battery (e.g. an ~7-8B
   model from a third lab - Mistral or Gemma are the obvious candidates) to
   separate "bigger models read faster" from "this family reads faster."
   Use `sweep.py --model <name>` exactly as-is; it is already resumable and
   deterministic. Add the new row to the comparison table in README.md only
   after running `analyze.py` on the fresh output and confirming the numbers
   match what gets written down.
2. **Test a third family properly**, not just a third data point - ideally
   at two sizes of that family (e.g. a 3B and a 7-8B variant of the same new
   family) to see whether the qwen 3B-flat / 7B-climbing pattern is a qwen
   quirk or general.
3. **Extend beyond demographic attributes**, if that direction is wanted at
   all - this needs a deliberate decision first, since Beyond Memorization
   already covers income/location/employer inference and the ethical bar for
   testing those against real corpus authors (versus consenting live users in
   the two-seat app) is higher. Do not add new attributes to the app or the
   sweep without that decision being made explicitly and written down here.
4. Before any of the above, re-read RESULT.md's caveats section in full - the
   n=72 confidence intervals are wide enough that a new model landing a few
   points differently from the existing two is not automatically a
   disagreement worth a new headline.

## Files someone resuming should read first

- `RESULT.md` - the full record, including the replication and contamination
  sections appended at the end. Source of truth for every number.
- `PLAN.md` - the pre-registered gate and design decisions (sample
  construction, why star sign is the control, why the baseline is best
  constant guess and not 1/k).
- `README.md` - the public write-up, now current.
- `server.py` / `index.html` - the two-seat app; thresholds are hardcoded
  from the qwen sweep and documented as such in both files.
