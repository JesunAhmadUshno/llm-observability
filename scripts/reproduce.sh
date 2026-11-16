#!/bin/sh
# One-command reproduce: tests, the four runners, then check that the
# committed results came back unchanged (same check as CI).
# benchmark_reload_aggregate_ms is the one timing field allowed to differ.
set -e
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -v
python3 level-1-learn/run_learn.py
python3 level-2-build/run_build.py
python3 level-3-deep/run_deep.py
python3 level-3-deep/calibrate.py
git diff --exit-code -- level-1-learn/results_learn.json level-2-build/store_build.jsonl \
  level-2-build/dashboard.html level-3-deep/results_deep.json level-3-deep/results_calibration.json
if git diff -U0 -- level-2-build/results_build.json | grep '^[-+] ' | grep -v benchmark_reload_aggregate_ms; then
  echo "results_build.json changed beyond the timing field"; exit 1
fi
echo "Reproduced: every committed result matches."
