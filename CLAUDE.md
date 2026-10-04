# CLAUDE.md - COLD READ

Research repo: how many words a person writes before a local language model can infer who they are, with a labelled negative control (star sign) and a second-model replication. Archived report: DOI 10.5281/zenodo.22309660 (CC BY 4.0). The research flagship per `zaid-os/strategy/FLAGSHIPS.md`.
Doc of record: `RESULT.md` (findings) and `HANDOFF.md` (open work). Read `/research` command rules before touching the method.

## Run

| What | Command |
|---|---|
| Env | global Python 3.12+ is fine; `pip install -r requirements.txt` |
| Sweep (needs Ollama at 127.0.0.1:11434 with `qwen2.5:7b-instruct` / `llama3.1:8b`) | `python sweep.py --model qwen2.5:7b-instruct` (resumable JSONL in `out/`) |
| Hosted reader (OpenRouter, e.g. 70B) | `OPENROUTER_API_KEY` in the environment, then `python sweep.py --model meta-llama/llama-3.3-70b-instruct --provider openrouter --max-usd 0.20` (writes `out/results-openrouter-<model>.jsonl`; about $0.044 per full 504-call run at 2026-09-28 prices; hosted output is not bit-for-bit deterministic) |
| Analyze shipped results | `python analyze.py out/results-qwen2.5_7b-instruct.jsonl` (add `--json` for structured output) |
| Two-seat live app | `python server.py` then open http://127.0.0.1:8420 |
| Tests | `pytest -q` (smoke: analysis reproduces the headline numbers from the committed JSONL) |
| Verification scripts | `python verify_run.py`, `python contamination_check.py` |

## Deploy

- None; local-only by design (needs a local model). Cloud story: `.devcontainer/` for reading and re-analysis; the sweep itself needs a GPU box with Ollama.

## Definition of done (any change here)

- `pytest -q` green; if results changed, `RESULT.md` numbers regenerated from `analyze.py` output, never typed by hand.
- Any new claim has its control in the same table and is run on both model families before it is a headline.
- Ethics rule holds: the only attributes beyond gender and age band is industry (Zaid approved 2026-10-04, public corpus only, PLAN.md change log); no location, employer or income; the live app never infers industry and its consent gate stays.
- New deposit to Zenodo only with Zaid's explicit approval (it mints a new DOI version).

## Gotchas

- Never the em dash character (U+2014); use " - ". Never add Claude/Anthropic attribution anywhere.
- `out/*.log` are model-pull noise (gitignored); `data/` and root PNGs are gitignored, which is why the app screenshots are untracked - copy any needed screenshot into `docs/`.
- The README curve SVG is vendored in `docs/` (was loaded from the profile repo before 2026-09-15).
- Ollama at temperature 0 with a fixed seed is NOT deterministic here: isolated spot checks flip up to about 1 in 5 predictions, a full qwen re-run flipped 5% and a full llama 8B re-run 0% (aggregate hit counts barely move; see RESULT.md step 3). Never write "deterministic" or "identical" about a rerun without measuring it.
- `sweep.py --task industry` caps output at 200 tokens (`num_predict`) because llama3.2 3B otherwise runs away and burns the 600 s timeout per call. `--out` writes a replicate to a separate file; the resume logic skips rows already in the file, error rows included, so delete error rows before a retry.
