# Level 1, Learn: llm-observability

Status: DONE (2026-11-05). Request logging, tracing, and a prompt and
model version registry, built small with the Python standard library
only.

## Honest scope line

Every request in this level is simulated. No real LLM is called, no
service runs, and no dashboard exists yet. Token counts and latencies
are fixed in the labelled dataset (requests.json) so every number
below can be hand-checked. The price table holds stated teaching constants, not
live vendor prices.

## Teaching path

1. Start with cost. Read compute_cost in observability.py. Cost is
   (prompt tokens / 1000) times the input rate plus (completion
   tokens / 1000) times the output rate. The stated rates, in dollars
   per 1,000 tokens: alpha-small input 0.10, output 0.20; alpha-large
   input 0.50, output 1.00.
2. Then logging. RequestLogger.log_request builds one structured
   record per request: prompt, prompt hash (full sha256 of the prompt
   text), model, prompt and completion tokens, total tokens, cost,
   latency, and the prompt and model versions in use. Records export
   as JSON lines.
3. Then tracing. Tracer.span creates nested spans. A span records its
   parent, its children, and a duration read from an injected clock.
   Tests and the runner inject ManualClock, so durations are
   deterministic instead of wall-clock dependent.
4. Then the registry. VersionRegistry registers prompt and model
   versions, rejects duplicate versions, resolves a named version or
   the latest, lists versions, and keeps a changelog in registration
   order.
5. Then aggregation. aggregate computes count, token totals, total
   cost, mean latency, and p50 and p95 latency (nearest-rank method:
   rank = ceil(p / 100 * n), 1-indexed into the sorted values), plus
   the same summary per model.

## Run it

    python level-1-learn/run_learn.py
    python -m unittest tests.test_learn_observability -v
    python tests/test_smoke.py

The runner writes level-1-learn/results_learn.json deterministically:
run it twice and the file is identical (verified by hash, sha256
8c560904cf9b1ddc for the shipped run).

## Results (measured 2026-11-05, Muse VM, Python 3.12)

Main claim: on 10 simulated requests the logger recorded 22,750 total
tokens (15,500 prompt plus 7,250 completion) at a total cost of 9.80
USD from the stated price table, with mean latency 550.0 ms, p50
500 ms, and p95 1000 ms, across 20 trace spans (10 roots, each with
one model_call child), and 21 unit tests pass.

Per-request evidence (from results_learn.json):

| ID | Model | Prompt tokens | Completion tokens | Total tokens | Cost USD | Latency ms | Prompt version |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | alpha-small | 1000 | 500 | 1500 | 0.20 | 100 | v1 |
| R02 | alpha-small | 500 | 250 | 750 | 0.10 | 200 | v1 |
| R03 | alpha-large | 2000 | 1000 | 3000 | 2.00 | 300 | v1 |
| R04 | alpha-small | 2000 | 500 | 2500 | 0.30 | 400 | v1 |
| R05 | alpha-large | 1000 | 500 | 1500 | 1.00 | 500 | v2 |
| R06 | alpha-small | 1000 | 1000 | 2000 | 0.30 | 600 | v2 |
| R07 | alpha-large | 4000 | 2000 | 6000 | 4.00 | 700 | v2 |
| R08 | alpha-small | 500 | 500 | 1000 | 0.15 | 800 | v2 |
| R09 | alpha-large | 2000 | 500 | 2500 | 1.50 | 900 | v2 |
| R10 | alpha-small | 1500 | 500 | 2000 | 0.25 | 1000 | v2 |

Summary evidence:

| Measure | Value |
| --- | --- |
| Requests | 10 |
| Prompt tokens | 15,500 |
| Completion tokens | 7,250 |
| Total tokens | 22,750 |
| Total cost USD | 9.80 |
| Mean latency ms | 550.0 |
| p50 latency ms | 500 |
| p95 latency ms | 1000 |
| Trace spans | 20 (10 roots, 10 model_call children) |
| Registry changelog entries | 4 (prompt v1, prompt v2, alpha-small v1, alpha-large v1) |
| Cost labels matched | 10 of 10 (each computed cost equals the expected_cost_usd label in requests.json) |
| Unit tests | 21 passed, plus the scaffold smoke test |

Per-model evidence:

| Model | Count | Total tokens | Cost USD | Mean latency ms | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| alpha-small | 6 | 9,750 | 1.30 | 516.667 | 400 | 1000 |
| alpha-large | 4 | 13,000 | 8.50 | 600.0 | 500 | 900 |

Hand checks: R01 cost is (1000 / 1000) * 0.10 + (500 / 1000) * 0.20 =
0.10 + 0.10 = 0.20. R07 cost is (4000 / 1000) * 0.50 + (2000 / 1000)
* 1.00 = 2.00 + 2.00 = 4.00. Total cost is 0.20 + 0.10 + 2.00 +
0.30 + 1.00 + 0.30 + 4.00 + 0.15 + 1.50 + 0.25 = 9.80. Mean latency
is (100 + 200 + 300 + 400 + 500 + 600 + 700 + 800 + 900 + 1000) /
10 = 550.0. p50 is the 5th sorted latency (500) and p95 is the 10th
(1000) under the nearest-rank rule stated above.

## Failure modes and limits

- Simulated only: no real request, token count, or latency was
  measured from a live model. Real traffic is Build level scope.
- The set is small and fixed: 10 requests, 2 models, latencies in a
  clean 100 to 1000 ms ladder. Percentiles on 10 points are coarse.
- Price constants are teaching values stated in this README. They
  are not a vendor price list and drift from real prices over time.
- Everything is in-memory. Records, spans, and registry entries are
  lost when the process ends. No persistence, no dashboard.
- The registry stores version content but does not diff versions.
- Percentiles use the nearest-rank method only. Large streams would
  need an approximate sketch, which this level does not build.
- No quality drift detection or alerts. That is Deep level scope.
- This level was run on the Muse VM (CPU), not on its fleet node
  BlackBoxV2. That costs a grade deduction, named below.

## Grade

Grade: 8,700 of 10,000.

Deductions (named, summing to 1,300):
- Simulated requests only, no real LLM call or live service: minus 500.
- Small fixed set (10 requests, 2 models): minus 300.
- In-memory only, no persistence and no tracing dashboard: minus 200.
- Price table is stated teaching constants, not verified vendor
  prices: minus 150.
- Run on the Muse VM, not the fleet node BlackBoxV2: minus 100.
- No drift detection or alerts in this level (Deep scope): minus 50.

## What Build adds next

A real service that logs live requests end to end, persists records
and traces, and serves the tracing dashboard named in SPEC.md.
