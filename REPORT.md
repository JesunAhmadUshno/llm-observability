# REPORT: llm-observability (P12)

Field profile: Systems, reliability. Status: not pre-registered (see
PROPOSAL.md). Every request, token, latency and quality value in this
report is simulated; no real LLM was called. Runs were on the Muse VM
(CPU, Python 3.12), not the fleet node BlackBoxV2 named in the scaffold
spec.

Inside the moved sections, a mention of SPEC.md, LEARN-SPEC.md, NOVELTY.md,
DOSSIER.md or ROADMAP.md means the PROPOSAL.md section marked "was" that
file; a mention of a level README, the Deep README or the research review
means the REPORT.md section marked "was" that file.

## Summary

The repo builds, with the Python standard library only, a request
logger with tracing and a version registry (component 1), a persistent
JSONL-backed service with a static dashboard (component 2), and a
window-versus-window drift detector with alerts (component 3). On
seeded simulated windows of 1,000 records the detector stayed quiet on
the control and alerted on both injected drifts. A calibration study
over 50 seed pairs per setting shows where it fails: below 500 records
per window it false-alarms on most no-drift controls, and for small
latency shifts it is far less powerful than a two-sample KS test.

## Hypotheses scored (recorded after the fact, not pre-registered)

| Hypothesis | Result | Evidence |
| --- | --- | --- |
| H1 control raises no alert | Supported on the recorded run (0 alerts) and in calibration at N >= 500 (0/50, Wilson 95% 0.00 to 0.07). Missed at N = 100 (50/50 false alerts) and N = 200 (38/50). | level-3-deep/results_deep.json, level-3-deep/results_calibration.json |
| H2 latency and cost drift alerts | Supported (3 alerts, severity high) for the injected shift (latency mean shift 4.48 pooled SD). Missed for small shifts: a 0.25 SD latency shift alerted in 15/50 runs (0.19 to 0.44) against 50/50 for KS. | same files, power.latency_shift |
| H3 pass-rate drop alerts | Supported (1 alert, drop 0.281, z -14.896831). Missed for small drops: a 0.04 drop alerted in 11/50 (0.13 to 0.35). | same files, power.pass_rate_drop |

None of these is a test of the Systems, reliability profile: there are
no stated availability or recovery targets, no timed drill on a real
service, and no runbook. That is why the verdict stops at Functional.

## Numbers without evidence in the repo

- The reload-plus-aggregate benchmark (2.341 ms) was measured on the
  Muse VM and is a timing field; CI regenerates it on a different
  machine and ignores it. Treat it as indicative only.
- The test counts quoted in the dated sections below (21, 39, 47) were
  counts at the time; the suite now has more tests.

## Logging and tracing (was Learn, level-1-learn/README.md)

Status: DONE (2026-11-05). Request logging, tracing, and a prompt and
model version registry, built small with the Python standard library
only.

### Honest scope line

Every request in this level is simulated. No real LLM is called, no
service runs, and no dashboard exists yet. Token counts and latencies
are fixed in the labelled dataset (requests.json) so every number
below can be hand-checked. The price table holds stated teaching constants, not
live vendor prices.

### Teaching path

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

### Run it

    python level-1-learn/run_learn.py
    python -m unittest tests.test_learn_observability -v
    python tests/test_smoke.py

The runner writes level-1-learn/results_learn.json deterministically:
run it twice and the file is identical (verified by hash, sha256
8c560904cf9b1ddc for the shipped run).

### Results (measured 2026-11-05, Muse VM, Python 3.12)

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

### Failure modes and limits

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
  BlackBoxV2. That is stated as a limit here.


### What Build adds next

A real service that logs live requests end to end, persists records
and traces, and serves the tracing dashboard named in SPEC.md.

## Persistent service (was Build, level-2-build/README.md)

Status: DONE (2026-11-05). A persistent observability service that
logs simulated requests end to end, persists records and traces to
a JSONL store, diffs registry versions, and generates a static
tracing dashboard, built with the Python standard library only.

### Honest scope line

Every model call in this level is simulated. No real LLM is called
and no live network service runs. Token counts use a stated
deterministic proxy, not a real tokenizer: proxy tokens are
ceil(len(text) / 4), minimum 1 for non-empty text, 0 for empty
text. The price table holds stated teaching constants from Level 1,
not live vendor prices: alpha-small input 0.10, output 0.20;
alpha-large input 0.50, output 1.00, in dollars per 1,000 tokens.

### Method

1. Persistence. LogStore in service.py appends records and spans
   to one JSONL file. Each line is a JSON object tagged with a type
   of record or span. Load methods reload records and spans in
   order, skip corrupt lines, and count how many were skipped.
2. Service. ObservabilityService.handle_request runs one simulated
   request through nested trace spans: a root request span plus
   two child spans (prepare and model_call). Latency is the root
   span duration, taken from an injected ManualClock, so tests and
   the runner are deterministic. It computes prompt and completion
   tokens with the proxy above, computes cost from the Learn price
   table, persists the record and all spans, and returns the record
   with its spans attached.
3. Registry diff. diff_text compares two text versions line by
   line (added, removed, unchanged count). diff_entries compares
   dict contents by field (added, removed, changed, unchanged
   fields) and text contents by line. registry_diff resolves two
   versions from the Learn VersionRegistry and diffs them.
4. Dashboard. generate_dashboard (also re-exported from
   dashboard.py) aggregates stored records with the Learn aggregate
   function and writes a static HTML dashboard: measured totals,
   a per-model table, p50 and p95 latency, a request list, and a
   span list. The HTML file is a build artifact regenerated by
   run_build.py, not hand-written evidence.
5. Runner. run_build.py builds a registry (prompt v1 and v2, both
   models at v1), runs 60 deterministic simulated requests across
   2 models and 2 prompt versions, persists to
   store_build.jsonl, reloads from disk, aggregates, generates
   dashboard.html, and writes results_build.json.

### Run it

    python3 level-2-build/run_build.py
    python3 -m unittest discover -s tests -v
    python3 tests/test_smoke.py

Determinism: run_build.py run twice produces an identical
results_build.json except one explicitly named timing field,
benchmark_reload_aggregate_ms. That field is a measured benchmark
on the host and is not part of any determinism claim. This was
verified in this build by running twice and diffing the parsed
JSON: only benchmark_reload_aggregate_ms differed.

### Results (measured 2026-11-05, Muse VM, Python 3.12)

Main claim: on 60 simulated requests the service persisted and
reloaded 60 records and 180 trace spans (60 roots, each with
prepare and model_call children), totalling 2,208 proxy tokens
(876 prompt plus 1,332 completion) at a total cost of 1.062 USD
from the stated price table, with mean latency 333.167 ms, p50
315 ms, and p95 561 ms. Corrupt lines on reload: 0. Tests: 39
passed in total (21 Learn, 18 Build) plus the scaffold smoke test.

| Measure | Value |
| --- | --- |
| Requests | 60 |
| Prompt tokens (proxy) | 876 |
| Completion tokens (proxy) | 1,332 |
| Total tokens (proxy) | 2,208 |
| Total cost USD | 1.062 |
| Mean latency ms | 333.167 |
| p50 latency ms | 315 |
| p95 latency ms | 561 |
| Trace spans | 180 (60 roots, 120 children) |
| Spans per request | 3 |
| Prompt versions | v1 (30 requests), v2 (30 requests) |
| Corrupt lines on reload | 0 |
| Registry diff prompt v1 to v2 | added: Cite the source line.; removed: none; unchanged: 2 lines |
| Unit tests | 39 passed (21 Learn plus 18 Build), plus smoke test |
| Benchmark reload plus aggregate | 2.341 ms, measured on the Muse VM over the persisted 60 records and 180 spans; timing only, not deterministic |

Per-model evidence:

| Model | Count | Prompt tokens | Completion tokens | Total tokens | Cost USD | Mean latency ms | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| alpha-small | 30 | 438 | 666 | 1,104 | 0.177 | 263.0 | 244 | 392 |
| alpha-large | 30 | 438 | 666 | 1,104 | 0.885 | 403.333 | 397 | 585 |

Per-request hand checks: B01 prompt is 54 characters, so proxy
prompt tokens are ceil(54 / 4) = 14. Its completion is 91
characters, so proxy completion tokens are ceil(91 / 4) = 23.
Cost for B01 on alpha-small is (14 / 1000) * 0.10 + (23 / 1000)
* 0.20 = 0.0014 + 0.0046 = 0.006 USD, matching the record. B02
on alpha-large has 13 prompt and 22 completion proxy tokens:
(13 / 1000) * 0.50 + (22 / 1000) * 1.00 = 0.0065 + 0.022 =
0.0285 USD, matching the record. A unit test also hand-checks a
small case: prompt abcd is 1 proxy token and completion abcdefgh
is 2 proxy tokens, cost (1 / 1000) * 0.10 + (2 / 1000) * 0.20 =
0.0005 USD on alpha-small.

### Failure modes and limits

- Simulated only: no real LLM call, no live traffic, and no
  network server. A real deployment would need a server front
  end, authentication, and backpressure, none of which is here.
- Token proxy: ceil(len / 4) is a rule of thumb, not a tokenizer.
  Real token counts differ by model and by text.
- Price constants are teaching values, not a vendor price list.
- Dashboard is one static HTML file generated from stored
  records. There is no live refresh, query API, or filtering.
- The JSONL store is a single local file with no locking, no
  indexing, and no rotation. Concurrent writers could corrupt
  lines; the loader skips and counts corrupt lines instead of
  repairing them, which the tests cover.
- Percentiles use the Learn nearest-rank method only.
- No quality drift detection or alerts. That is Deep scope.
- This level was run on the Muse VM, not on its fleet node
  BlackBoxV2. That is stated as a limit here.


### What Deep adds next

Quality drift detection and alerts per SPEC.md: track quality
signals over time per prompt and model version, detect drift
against a baseline, and raise alerts when drift crosses a stated
threshold, with the failure modes written and the dossier updated
to ship state.

## Drift detection (was Deep, level-3-deep/README.md)

Status: DONE 2026-11-05

Quality drift detection and alerts over request-log windows, stdlib only. Quality is a simulated logged field (quality_pass) in every window and in every result. It is labelled simulated everywhere and is never presented as real model quality.

### Method

- drift.py compares a baseline window against a current window on latency_ms, total_tokens, cost_usd, and the simulated quality pass rate.
- Population Stability Index (PSI): baseline quantile bins (10 bins), smoothed proportions, for latency, tokens, and cost. PSI warning 0.10, alert 0.25, documented constants from common drift practice.
- Mean shift in pooled standard deviation units: for latency, tokens, and cost. Warning 0.5, alert 1.0, documented constants.
- Two-proportion z check: for the simulated quality pass rate. Alert requires a drop of at least 0.10 and absolute z at least 1.96. Warning drop is 0.05.
- Per-metric severity is the higher of its PSI and mean-shift signals for numeric metrics, or the pass-rate rule for quality. Alerts list every metric whose severity is medium or high.
- run_deep.py is a seeded, labelled simulated experiment: baseline (seed 1201), control with no drift (seed 2202, same distribution), latency-and-cost drift (seed 3203, latency mean 850, tokens mean 2200, cost per token 0.0009), and quality drift (seed 4204, simulated pass rate target 0.62 versus baseline 0.92). Each window has 1000 records. Window size was raised from an initial 200 to 1000 after the first run showed PSI sampling noise firing medium alerts on the control at 200; that change and its reason are recorded here, not hidden.

### Measured results (2026-11-05, Muse VM, Python 3.12)

Success criteria: all passed. Control: no alert. Latency-cost drift: alert fired. Quality drift: alert fired.

| Window | Metric | Baseline mean or rate | Current mean or rate | PSI | Mean shift (pooled SD) | Pass drop / z | Severity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| control_no_drift | latency_ms | 498.367 | 501.574 | 0.025905 | 0.040373 | n/a | none |
| control_no_drift | total_tokens | 1503.243 | 1504.807 | 0.009285 | 0.005343 | n/a | none |
| control_no_drift | cost_usd | 0.900578 | 0.903269 | 0.009807 | 0.014681 | n/a | none |
| control_no_drift | quality_pass_rate_simulated | 0.909 | 0.933 | n/a | n/a | -0.024 / 1.989541 | none |
| latency_cost_drift | latency_ms | 498.367 | 853.770 | 8.045714 | 4.480065 | n/a | high |
| latency_cost_drift | total_tokens | 1503.243 | 2194.422 | 4.427765 | 2.339562 | n/a | high |
| latency_cost_drift | cost_usd | 0.900578 | 1.972592 | 8.283089 | 4.433347 | n/a | high |
| latency_cost_drift | quality_pass_rate_simulated | 0.909 | 0.895 | n/a | n/a | 0.014 / -1.052923 | none |
| quality_drift | latency_ms | 498.367 | 512.586 | 0.051372 | 0.180196 | n/a | none |
| quality_drift | total_tokens | 1503.243 | 1515.399 | 0.002452 | 0.041302 | n/a | none |
| quality_drift | cost_usd | 0.900578 | 0.909820 | 0.006129 | 0.050293 | n/a | none |
| quality_drift | quality_pass_rate_simulated | 0.909 | 0.628 | n/a | n/a | 0.281 / -14.896831 | high |

Overall: control overall severity none with 0 alerts, latency_cost_drift overall high with 3 alerts, quality_drift overall high with 1 alert.

Tests: 47 passed in total (39 prior plus 8 Deep). Determinism: results_deep.json identical across two runs; it has no timing field.

### Run it

    python3 level-3-deep/run_deep.py
    python3 -m unittest discover -s tests -v

### Calibration over seeds

`python3 level-3-deep/calibrate.py` (stdlib, CPU, about 4 s) repeats the run_deep generator over 50 seed pairs per setting (repetition r uses baseline seed 10000 + 2r and current seed 10000 + 2r + 1) and writes `results_calibration.json`. All windows are simulated. Intervals are Wilson 95%.

False alerts on the no-drift control (any metric alerting, 10 PSI bins):

| Records per window | Runs with any alert | Wilson 95% |
| --- | --- | --- |
| 100 | 50/50 | 0.93 to 1.00 |
| 200 | 38/50 | 0.63 to 0.86 |
| 500 | 0/50 | 0.00 to 0.07 |
| 1,000 | 0/50 | 0.00 to 0.07 |
| 2,000 | 0/50 | 0.00 to 0.07 |

Detection power at N = 1,000 for a latency shift (repo rule: PSI or mean-shift alert; baseline: two-sample KS rejecting at alpha 0.05/3, asymptotic critical value):

| Shift ms (SD) | Repo rule | KS baseline |
| --- | --- | --- |
| 5 (0.0625) | 0/50 (0.00 to 0.07) | 7/50 (0.07 to 0.26) |
| 10 (0.125) | 0/50 (0.00 to 0.07) | 28/50 (0.42 to 0.69) |
| 20 (0.25) | 15/50 (0.19 to 0.44) | 50/50 (0.93 to 1.00) |
| 40 (0.5) | 50/50 (0.93 to 1.00) | 50/50 (0.93 to 1.00) |
| 80 (1) | 50/50 (0.93 to 1.00) | 50/50 (0.93 to 1.00) |

Detection power at N = 1,000 for a simulated pass-rate drop (repo rule: drop and |z| threshold; Bonferroni: the survives_bonferroni field of detect_drift, two-sided |z| at alpha 0.05/4):

| True drop | Repo rule | Bonferroni z |
| --- | --- | --- |
| 0.02 | 0/50 (0.00 to 0.07) | 7/50 (0.07 to 0.26) |
| 0.04 | 11/50 (0.13 to 0.35) | 34/50 (0.54 to 0.79) |
| 0.06 | 37/50 (0.60 to 0.84) | 50/50 (0.93 to 1.00) |
| 0.08 | 50/50 (0.93 to 1.00) | 50/50 (0.93 to 1.00) |
| 0.1 | 50/50 (0.93 to 1.00) | 50/50 (0.93 to 1.00) |
| 0.12 | 50/50 (0.93 to 1.00) | 50/50 (0.93 to 1.00) |

A one-sided CUSUM (k = 0.5 SD, h = 5 SD) on a latency stream of 500 records before and 500 after a 40 ms shift false-alarmed before the change in 21/50 runs, detected the change in 29 of the rest, and missed 0. Median detection delay 32 records (range 5 to 131).

What this shows: on this generator the thresholds are too sensitive below about 500 records per window, and the PSI / mean-shift rule is much less powerful than KS for small latency shifts. It says nothing about real traffic.

### Failure modes

- Simulated only: all windows are synthetic. A detector that separates these seeded windows may fail on real traffic with seasonality, model mix changes, or correlated incidents.
- Small windows: at 200 records per window PSI fired medium alerts on the no-drift control in the first run. Small samples inflate PSI. Production use needs larger windows or fewer bins, stated before use.
- Bin edge sensitivity: PSI depends on baseline quantile bins. A baseline with many duplicate values collapses bins and weakens the score.
- Quality field limits: quality_pass is a single simulated boolean. Real quality is graded, delayed, and often human judged; a pass-rate drop can reflect labelling delay, not model change.
- Threshold limits: thresholds are documented constants, not learned. They will be wrong for some real distributions and need calibration per service.
- Cost and tokens are correlated here by construction (cost derives from tokens). Alerting on both can double-count one underlying change.
- No alert delivery: alerts are data in JSON and return values only. No email, webhook, or paging channel exists in this level.
- One-sided quality check: the pass-rate rule alerts only on drops (current below baseline). A rise in pass rate never alerts, by design.
- Distribution shape: mean shift misses shape changes with the same mean; PSI catches some of those, but neither statistic proves a cause.

## Review (2026-11-07, was docs/research-review.md)

Reviewed 2026-11-07. The review covers the repo as it stands on the `site/live-dashboard` branch, including the calibration study (`level-3-deep/calibrate.py`) and the live dashboard (`site/`). Every number quoted here is in a committed results file.

**Bottom line:** a clean, deterministic, well-tested teaching build of LLM request logging, tracing and drift detection. As research it is a simulation study: it shows the detector separates distributions the author built to be separable, and now measures how often it false-alarms and how much power it has, on that same generator. It makes no claim about real LLM traffic, and should not.

| Criterion | Evidence | Gap |
| --- | --- | --- |
| Research question | Deep asks: can PSI, pooled-SD mean shift and a two-proportion z flag latency, cost and quality drift between windows of logged requests? | The question is about a generator, not about production LLM drift. No question about which detector is best for which drift type is stated up front. |
| Hypotheses | Implicit: control stays quiet, injected drifts alert. Met on the recorded run (control 0 alerts; latency-cost drift 3 alerts; quality drift 1 alert, pass rate 0.909 to 0.628, z -14.9). | No pre-registered hypotheses or effect sizes of interest. Thresholds were fixed before the run, which helps. |
| Method | Baseline-quantile PSI with EPS smoothing, mean shift in pooled SD, two-proportion z, severity rules with stated reasons (`level-3-deep/drift.py`). | Thresholds are literature constants (PSI 0.10/0.25, 0.5/1.0 SD, drop 0.05/0.10 with z 1.96), not learned. The pass-rate check is one-sided (drops only), now documented. |
| Baselines | Fixed now: two-sample KS per numeric metric and a one-sided CUSUM on a latency stream, in `calibrate.py`. KS is clearly more powerful for small latency shifts (see Deep README table). | No comparison with an existing observability tool (Langfuse class). `NOVELTY.md` still says NO MEASUREMENT YET. |
| Statistics and uncertainty | Fixed now: false-alert rate and detection power over 50 seed pairs per setting with Wilson 95% intervals; Bonferroni z field (alpha/4) and KS at alpha/3. | 50 runs give wide intervals (0/50 still allows up to 7%). Cost and tokens are correlated by construction, so the four tests are not independent. |
| Reproducibility | Seeded stdlib generators; CI runs every level's tests and runners and fails if any committed result changes (one named timing field excepted). Verified locally on 2026-11-07: `run_deep.py` and `calibrate.py` reproduce their JSON byte for byte. The site's build re-runs the detector in JavaScript (exact MT19937 port) and fails if it does not match `results_deep.json` and the false-alert counts. | None at this scale. |
| Threats to validity | Level READMEs list failure modes: simulated only, small windows, bin-edge sensitivity, boolean quality, cost/token double counting, no alert delivery. | External validity is the main threat and is not addressable without real traffic. |
| Related work | PSI, KS and CUSUM (Page, 1954) are standard; Wilson (1927) intervals. | `DOSSIER.md` defers prior art; there is no dated literature review of LLM observability or drift detection. |
| Limitations stated | Every level states simulated traffic, teaching price constants, the ceil(len/4) token proxy. | Runs were on the Muse VM, not the fleet node in SPEC (stated in this report). |
| Engineering rigor | 58 tests (`python3 -m pytest -q`), ruff lint, 3.11 and 3.12 matrix, deterministic artifacts, stdlib only. | Learn's 10 requests sit on a clean 100 to 1000 ms ladder, so percentiles there are trivial. |

### Fixed during the review (cheap, CPU, seconds)

1. Dead branch in `two_proportion_z` (`z = 0.0 if p1 == p2 else 0.0`) removed, with zero-SE tests.
2. KS baseline and Bonferroni fields added to `detect_drift` output; `results_deep.json` alert outcomes unchanged.
3. Calibration study (`calibrate.py`, `results_calibration.json`): false alerts on the control are 50/50 at N = 100 and 38/50 at N = 200, then 0/50 from N = 500. This quantifies the README's old note that PSI fired on the control at 200 records.
4. CI now runs the Deep tests, `run_deep.py` and `calibrate.py`, and checks the committed results reproduce.
5. `docs/index.md` no longer says "Deep: not started".
6. Deep README states the one-sided pass-rate check and carries the calibration tables.
7. The dashboard re-runs the detector live, with build-time parity checks (`site/src/drift.check.mjs`, `site/src/obs.check.mjs`).

## Conclusion

On its own generator, the drift rule does what it was built to do at
1,000 records per window and fails in measured, reported ways below
500 records and for small shifts. It says nothing about real LLM
traffic. The next step, and what a confirmatory cycle must lock first,
is in PROPOSAL.md under "Next cycle".
