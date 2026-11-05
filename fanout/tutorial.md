# Tutorial: P12 llm-observability, course module

Module: P12-llm-observability
By Jesun Ahmad Ushno
Date: 2026-11-05
License for this tutorial: CC BY 4.0. Code in the repo: Apache-2.0.

## What you will do

You will clone the llm-observability repo, run all three levels,
run the test suite for each level, and read your own results
against the recorded v1.0 numbers. Every command below exists in
the repo as shipped at v1.0 and was run by the author of this
module on 2026-11-05 to verify it. The project needs Python 3.11
or 3.12 and uses the standard library only. No model, no API, and
no credential are needed. Every request is simulated and no real
LLM is called.

All recorded numbers in this module come from simulated data. They
prove the logging, tracing, registry, persistence, and drift
machinery. They do not prove production quality, and quality in
Deep is a simulated logged field, never real model quality.

## Step 0: Clone and enter the repo

```text
git clone https://github.com/JesunAhmadUshno/llm-observability.git
cd llm-observability
```

## Step 1: Level 1, Learn, logging, tracing, registry

Read level-1-learn/README.md first. It explains cost from the
stated teaching price table, the structured request record, nested
trace spans from an injected clock, the version registry, and
aggregation with nearest-rank percentiles.

Run the Learn task set:

```text
python3 level-1-learn/run_learn.py
```

Run the Learn tests:

```text
python3 -m unittest tests.test_learn_observability -v
```

Run the scaffold smoke test:

```text
python3 tests/test_smoke.py
```

Read your results:

- Expected summary: 10 simulated requests, 22,750 total tokens
  (15,500 prompt plus 7,250 completion), total cost 9.80 USD,
  cost labels matched 10 of 10, mean latency 550.0 ms, p50 500 ms,
  p95 1000 ms, 20 spans with 10 roots.
- Expected tests: 21 tests, all passing.
- Expected smoke test line: scaffold smoke test PASS.

## Step 2: Level 2, Build, persistent service and dashboard

Read level-2-build/README.md. The service persists records and
spans to a JSONL store, runs each simulated request through three
nested spans, counts tokens with the proxy ceil(len(text) / 4)
(not a real tokenizer), diffs registry versions, and generates a
static HTML dashboard.

Run the Build task set:

```text
python3 level-2-build/run_build.py
```

Run the Build tests:

```text
python3 -m unittest tests.test_build_service -v
```

Read your results:

- Expected summary: 60 simulated requests, 2,208 proxy tokens
  (876 prompt plus 1,332 completion), total cost 1.062 USD, mean
  latency 333.167 ms, p50 315 ms, p95 561 ms, 180 spans, corrupt
  lines 0.
- Expected registry diff, prompt v1 to v2: added Cite the source
  line., removed none, unchanged 2 lines.
- The runner writes level-2-build/results_build.json,
  level-2-build/store_build.jsonl, and
  level-2-build/dashboard.html. The results file is identical
  across runs except benchmark_reload_aggregate_ms, a timing field.
- Expected tests: 18 Build tests, all passing, 39 in total.

## Step 3: Level 3, Deep, drift detection and alerts

Read level-3-deep/README.md. The detector compares a baseline
window with a current window using PSI and mean shift for latency,
tokens, and cost, and a two-proportion z check for the simulated
quality pass rate. Quality is a simulated logged field.

Run the Deep experiment:

```text
python3 level-3-deep/run_deep.py
```

Run the Deep tests:

```text
python3 -m unittest tests.test_deep_drift -v
```

Read your results:

- Each window holds 1,000 records. Success criteria: all passed.
- Expected control: overall severity none, 0 alerts, latency PSI
  0.025905.
- Expected latency and cost drift: overall severity high, 3 alerts,
  latency PSI 8.045714, latency mean shift 4.480065, latency mean
  498.367 to 853.770 ms.
- Expected quality drift: overall severity high, 1 alert,
  simulated pass rate 0.909 to 0.628, drop 0.281.
- The runner writes level-3-deep/results_deep.json, identical
  across two runs with no timing field.
- Expected tests: 8 Deep tests, all passing, 47 in total.

## Step 4: Run the full test suite

```text
python3 -m unittest discover -s tests -v
```

Expected: 47 tests in total (21 Learn, 18 Build, 8 Deep), all
passing, plus the scaffold smoke test.

## Step 5: Check your understanding

1. Why does Build call its token counts a proxy? (Answer: they are
   ceil(len(text) / 4), a rule of thumb, not a real tokenizer. Real
   counts differ by model and by text, so the README states the
   proxy wherever the Build numbers appear.)
2. Why was the Deep window size raised from 200 to 1,000 records?
   (Answer: at 200 records, PSI sampling noise fired medium alerts
   on the no-drift control in the first run. Small samples inflate
   PSI, so the shipped experiment uses 1,000 records per window
   and records the change and its reason.)
3. A Deep quality alert fires. Why does that not prove the model
   got worse? (Answer: quality_pass is a simulated boolean field
   in this project, and in real traffic a pass-rate drop can also
   reflect labelling delay or a mix change. The alert is a signal
   to investigate, not a cause.)

## Limits to keep with the numbers

- Simulated data only, at every level. No real LLM is called.
- Build token counts are the ceil(len/4) proxy, not a tokenizer.
- The price table is stated teaching constants, not vendor prices.
- Deep quality is a simulated logged field, not real model quality.
- Drift thresholds are documented constants, not learned values.
