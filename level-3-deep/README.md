# Level 3, Deep: llm-observability

Status: DONE 2026-11-05

Quality drift detection and alerts over request-log windows, stdlib only. Quality is a simulated logged field (quality_pass) in every window and in every result. It is labelled simulated everywhere and is never presented as real model quality.

## Method

- drift.py compares a baseline window against a current window on latency_ms, total_tokens, cost_usd, and the simulated quality pass rate.
- Population Stability Index (PSI): baseline quantile bins (10 bins), smoothed proportions, for latency, tokens, and cost. PSI warning 0.10, alert 0.25, documented constants from common drift practice.
- Mean shift in pooled standard deviation units: for latency, tokens, and cost. Warning 0.5, alert 1.0, documented constants.
- Two-proportion z check: for the simulated quality pass rate. Alert requires a drop of at least 0.10 and absolute z at least 1.96. Warning drop is 0.05.
- Per-metric severity is the higher of its PSI and mean-shift signals for numeric metrics, or the pass-rate rule for quality. Alerts list every metric whose severity is medium or high.
- run_deep.py is a seeded, labelled simulated experiment: baseline (seed 1201), control with no drift (seed 2202, same distribution), latency-and-cost drift (seed 3203, latency mean 850, tokens mean 2200, cost per token 0.0009), and quality drift (seed 4204, simulated pass rate target 0.62 versus baseline 0.92). Each window has 1000 records. Window size was raised from an initial 200 to 1000 after the first run showed PSI sampling noise firing medium alerts on the control at 200; that change and its reason are recorded here, not hidden.

## Measured results (2026-11-05, Muse VM, Python 3.12)

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

## Run it

    python3 level-3-deep/run_deep.py
    python3 -m unittest discover -s tests -v

## Calibration over seeds

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

## Failure modes

- Simulated only: all windows are synthetic. A detector that separates these seeded windows may fail on real traffic with seasonality, model mix changes, or correlated incidents.
- Small windows: at 200 records per window PSI fired medium alerts on the no-drift control in the first run. Small samples inflate PSI. Production use needs larger windows or fewer bins, stated before use.
- Bin edge sensitivity: PSI depends on baseline quantile bins. A baseline with many duplicate values collapses bins and weakens the score.
- Quality field limits: quality_pass is a single simulated boolean. Real quality is graded, delayed, and often human judged; a pass-rate drop can reflect labelling delay, not model change.
- Threshold limits: thresholds are documented constants, not learned. They will be wrong for some real distributions and need calibration per service.
- Cost and tokens are correlated here by construction (cost derives from tokens). Alerting on both can double-count one underlying change.
- No alert delivery: alerts are data in JSON and return values only. No email, webhook, or paging channel exists in this level.
- One-sided quality check: the pass-rate rule alerts only on drops (current below baseline). A rise in pass rate never alerts, by design.
- Distribution shape: mean shift misses shape changes with the same mean; PSI catches some of those, but neither statistic proves a cause.

## Grade

Grade: 8,500 of 10,000.

Deductions:
- Simulated only and no real LLM or live service: minus 500.
- Quality field is simulated (a boolean pass flag, not measured model quality): minus 300.
- Run on Muse VM, not BlackBoxV2 (the fleet node in SPEC): minus 200.
- Thresholds are documented constants, not learned or calibrated on real data: minus 300.
- No alert delivery channels and no output-text or embedding drift: minus 200.
Total deductions: 1,500.
