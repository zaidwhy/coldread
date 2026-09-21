# Contributing

COLD READ is a small research repo. The most useful contribution is a replication: run the same sample, prompt and seed on another model and report what happens, especially if it disagrees.

## Run a new model

You need Ollama running locally and the Blog Authorship Corpus CSV at `data/blogtext.csv`. `data/` is gitignored, so the corpus and the built sample are not in the repo; `build_sample.py` rebuilds the same 72-author sample deterministically (seed 1938). The existing results are committed under `out/`.

```powershell
pip install -r requirements.txt
python build_sample.py                 # only if data/sample.json is missing
python sweep.py --model mistral:7b     # 504 calls, resumable
python analyze.py out/results-mistral_7b.jsonl
```

`scripts/run_model_sweep.ps1 -Model <name>` does the whole thing unattended, including pulling the model and rerunning any failed rows. Do not change the sample, the prompt, the seed or the word counts for a replication, or the curves stop being comparable.

## Rules

- Every published number comes from `analyze.py` output, never typed by hand. If results change, regenerate the tables in `RESULT.md` and the README from it.
- A new claim needs its control in the same table and has to hold on a second model before it is a headline.
- Ethics: only gender and age band, which are self-reported labels in the corpus. No occupation or location attributes, in the sweep or in the app. Adding one needs a written decision first.
- The sample is small (n = 72), so read the intervals before calling a difference between models real.

## Before you open a pull request

```powershell
pytest -q
```

CI runs the same smoke test. Keep the change to what the pull request describes, and do not use the em dash character in any file. Use " - " instead.

## Reporting a problem

Use the issue templates: one for a bug and one for a replication result.
