# Changelog

Newest first. The four `v1.0.x` tags all landed on 2026-09-05 as the report was prepared for its Zenodo deposit. Study work before that is dated from the git history.

## Unreleased

- Added `docs/ARCHITECTURE.md`, `CONTRIBUTING.md`, issue templates and this changelog.
- Added `scripts/run_model_sweep.ps1`: unattended pull, sweep, retry of failed rows and analysis for one model, with a status file.
- Started a third model family run (`mistral:7b`) on 2026-09-21. Its result is not yet in `RESULT.md` or the README.
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
