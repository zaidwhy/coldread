#!/usr/bin/env bash
# Step 4 runner: each reader under both fixed option orders, one model on disk at a time.
# Usage: bash scripts/run_crossed.sh   (resumable; a reader is removed only after 504 clean rows per order)
set -u
cd "$(dirname "$0")/.."
# Two copies appending to one results file duplicate rows (it happened once); allow a single runner.
mkdir out/.crossed.lock 2>/dev/null || { echo "another run_crossed.sh holds out/.crossed.lock"; exit 3; }
trap 'rmdir out/.crossed.lock' EXIT
MIN_FREE_GB=7   # a 7-8B reader is about 5 GB; never pull into a nearly full disk

free_gb() { df -BG --output=avail . | tail -1 | tr -dc '0-9'; }

sweep_order() {  # model order -> echoes "rows bad"
  local model=$1 order=$2 slug=$3 file="out/results-crossed-$2-$3.jsonl"
  for attempt in 1 2; do
    # sweep.py skips rows already in the file, error rows included, so drop those before a retry
    if [ -f "$file" ]; then grep -v '"pred": null' "$file" > "$file.keep"; mv "$file.keep" "$file"; fi
    python -u sweep.py --model "$model" --order "$order" >> "out/run-crossed-$order-$slug.log" 2>&1
    [ "$(grep -c '"pred": null' "$file")" -eq 0 ] && break
  done
  echo "$(wc -l < "$file") $(grep -c '"pred": null' "$file")"
}

for model in llama3.1:8b qwen2.5:7b-instruct mistral:7b; do
  slug=$(echo "$model" | tr ':/' '__')
  if [ "$(wc -l < "out/results-crossed-listed-$slug.jsonl" 2>/dev/null || echo 0)" -eq 504 ] \
     && [ "$(wc -l < "out/results-crossed-reversed-$slug.jsonl" 2>/dev/null || echo 0)" -eq 504 ] \
     && ! grep -q '"pred": null' out/results-crossed-*-"$slug".jsonl; then
    echo "$model already complete"; continue
  fi
  if ! ollama list | grep -qF "$model"; then
    until [ "$(free_gb)" -ge "$MIN_FREE_GB" ]; do echo "waiting for disk: $(free_gb) GB free"; sleep 120; done
    ollama pull "$model" > "out/pull-crossed-$slug.log" 2>&1 || { echo "pull failed: $model"; exit 1; }
    ollama list | grep -F "$model" >> out/crossed-model-digests.txt
  fi
  clean=1
  for order in listed reversed; do
    read -r rows bad <<< "$(sweep_order "$model" "$order" "$slug")"
    echo "$model $order rows=$rows unparsed_or_error=$bad"
    [ "$rows" -eq 504 ] && [ "$bad" -eq 0 ] || clean=0
  done
  if [ "$clean" -eq 1 ]; then ollama rm "$model"; else echo "stopping: $model rows need a look"; exit 2; fi
done
echo "all readers done"
