---
name: Replication result
about: Report what happened when you ran the same sweep on another model
title: "[replication] "
labels: replication
---

## Model

Exact Ollama tag (for example `mistral:7b`), its size, and the lab that trained it.

## Setup

- [ ] Same sample (`build_sample.py`, seed 1938), same prompt, same seed, same word counts. If anything differed, say what.
- Number of records and unparsed replies from the `analyze.py` header:

## Result

Paste the `analyze.py` table. State the half-life you read from it for gender and age band, and whether star sign stayed at its floor.

## Does it agree with the existing two models?

Say plainly if it agrees, disagrees, or is within the wide intervals of n = 72. A disagreement is welcome and will be reported as such.
