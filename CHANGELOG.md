# Changelog

Newest first. The four `v1.0.x` tags all landed on 2026-09-05 as the report was prepared for its Zenodo deposit. Study work before that is dated from the git history.

## Unreleased

- Step 3b, topic-word masking (pre-registered in PLAN.md before any masked result): with the industry-word lexicon masked, llama3.1:8b half-life 25 to 50 words and qwen2.5:7b 50 to 100, plateaus within 5 points, control clean; case (a) of the pre-registered rule in both families. RESULT.md, `out/results-industry-masked-*.jsonl`, test. Not yet deposited.

## v1.3.0 - 2026-10-06

- Step 3, industry as a fourth attribute (adults only, four industries, 72 authors, 25% constant guess), run on the same four readers with star sign as the control. Half-lives 25 (llama3.1:8b), 50 (qwen2.5:7b), 50 (mistral:7b), 200 (llama3.2 3B, weak, 27 of 504 unparsed); plateau about 42 to 51%; control clean for all four. Written into RESULT.md, README, CITATION and the Zenodo description. Pre-registration in `PLAN.md`; `tests/test_industry.py`.
- Determinism correction: Ollama at temperature 0 with a fixed seed is not fully deterministic here. Full re-runs reproduced the half-lives (qwen 25 of 504 predictions differ, llama 8B 0).
- `sweep.py --provider openrouter` for hosted readers, with a spend cap.
- Pre-registered for later, not part of this deposit: the topic-word masking test (`PLAN.md` step 3b, `topicmask.py`, `sweep.py --mask-topic`). Its results are not in this version.

## v1.2.0 - 2026-09-27

- Two sizes of one family: `llama3.2` (3B) against `llama3.1:8b`, identical protocol; 501/504 rows (3 deterministic timeouts, reported). Gender never clears at 3B (50 words at 8B); age band 100 words (25 at 8B). RESULT.md section, `out/results-llama3.2_latest.jsonl`, `out/analysis-llama3.2_latest.txt`, smoke test (12 passed). Deposited as Zenodo v1.2.0.
- `analyze.py --json`: the same analysis as structured output (per-step hits, totals, accuracy, Wilson bounds, clears-baseline flag, half-lives), so tables can be generated instead of typed. The text report is byte-identical to before; tests check the JSON against the committed results.

## v1.1.0 - 2026-09-27

- Third model family written up: `mistral:7b` (same 7-8B class, identical sample, seed and prompt) in `RESULT.md`, README, Zenodo description and CITATION. Gender half-life 50 / 800 / 1600 words across the three readers (thirty-two-fold at one size); the shared ~60% age ceiling is withdrawn; the below-chance dip is not supported in any model. Smoke test covers all three result files.
- Added `docs/ARCHITECTURE.md`, `CONTRIBUTING.md`, issue templates and this changelog.
- Added `scripts/run_model_sweep.ps1`: unattended pull, sweep, retry of failed rows and analysis for one model, with a status file.
- Third model family (`mistral:7b`): started 2026-09-21, completed 2026-09-22 (504/504, 0 unparsed; `out/results-mistral_7b.jsonl`, `out/analysis-mistral_7b.txt`). Written up in v1.1.0.
- Declared dependencies, added an analysis smoke test with CI, vendored the README chart into `docs/`, added `CLAUDE.md` and `AGENTS.md`.

## v1.0.3 - 2026-09-05

- Deposited as a research report under CC BY 4.0 and declared the prior work it cites.

## v1.0.2 - 2026-09-05

- Sharpened the prior-work position by naming the classical length-sweep literature the result has to answer to.

## v1.0.1 - 2026-09-05

- Added the copyright and citation section and the result figure.

## v1.0.0 - 2026-09-05

- Added Zenodo deposit metadata for DOI archival (DOI 10.5281/zenodo.22309660), plus the DOI badge, `CITATION.cff` and ORCID authorship metadata.

## 2026-08-23 and after - the study

- Measured the curves on `qwen2.5:7b-instruct`, replicated on `llama3.1:8b`, and tested corpus memorisation directly.
- Wrote the public README leading with the finding, and the two-seat live app with its consent gate.
