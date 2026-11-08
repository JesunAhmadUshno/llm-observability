# Paper candidate brief: drift detection for logged LLM requests

Project: P12 llm-observability
Status: CANDIDATE, brief written 2026-11-05
Submission note: submission is Jesun's tap. Nothing is submitted by
this brief, and no venue has been contacted. The publications
tracker is updated by the coordinator, not by this file.

## Working title

Drift detection on logged LLM requests: PSI, mean shift, and a
pass-rate z check measured on seeded simulated windows, with a
window-size failure recorded

## Abstract draft

Based only on the measured v1.0 results recorded in the repo.
Numbers below are from simulated data and are stated as such. No
real LLM was called, and the quality field is a simulated logged
boolean, not real model quality.

LLM services change under their operators: latency, token use, and
cost drift, and answer quality can fall, while the request log is
often the only record that shows it. This work presents an open,
dependency-free observability stack and measures a drift detector
on seeded simulated windows. At Learn level, request logging,
tracing, and a version registry recorded 10 simulated requests
totalling 22,750 tokens at a cost of 9.80 USD from a stated
teaching price table, with mean latency 550.0 ms, 20 trace spans,
cost labels matched on 10 of 10 requests, and 21 unit tests. At
Build level, a persistent JSONL service over 60 simulated requests
persisted 180 trace spans totalling 2,208 proxy tokens
(ceil(len/4), not a real tokenizer) at a cost of 1.062 USD, with
mean latency 333.167 ms, p50 315 ms, and p95 561 ms, a registry
diff for prompt v1 to v2 that added "Cite the source line.", and
18 tests (39 in total). At Deep level, a detector using PSI, mean
shift in pooled standard deviation units, and a two-proportion z
check was run over windows of 1,000 records each: the control
window raised 0 alerts at severity none with latency PSI 0.025905,
the latency and cost drift window raised 3 alerts at severity high
with latency PSI 8.045714, mean shift 4.480065, and latency mean
498.367 to 853.770 ms, and the quality drift window raised 1 alert
at severity high with the simulated pass rate falling from 0.909
to 0.628, a drop of 0.281. The stack ships with 47 unit tests. The
windows are seeded and simulated, thresholds are documented
constants, and quality is simulated; the paper claims the detector
method and its measured separation on these windows, including the
recorded failure at 200 records per window, not performance on
real traffic.

## Method outline

1. Logging layer: one structured record per request (prompt, full
   sha256 prompt hash, model, token counts, cost from the stated
   price table, latency, prompt and model versions), with JSON
   lines export.
2. Tracing layer: nested spans with parent and children, durations
   read from an injected clock so runs are deterministic.
3. Registry layer: prompt and model versions registered in order,
   duplicates rejected, with line and field diffs between versions.
4. Build persistence: records and spans appended to one JSONL
   store, reloaded in order with corrupt lines skipped and counted,
   and aggregated with nearest-rank percentiles.
5. Drift statistics: PSI on baseline quantile bins (10 bins,
   smoothed proportions, warning 0.10, alert 0.25), mean shift in
   pooled standard deviation units (warning 0.5, alert 1.0), and a
   two-proportion z check for the simulated pass rate (alert needs
   a drop of at least 0.10 and absolute z at least 1.96).
6. Seeded experiment: baseline (seed 1201), control with no drift
   (seed 2202), latency and cost drift (seed 3203), and quality
   drift (seed 4204), each window 1,000 records, all labelled
   simulated in the results file.
7. Window-size record: the experiment first ran at 200 records per
   window, where PSI noise fired medium alerts on the control. The
   shipped run uses 1,000 records, and the change and its reason
   are recorded in REPORT.md.
8. Scoring: per-metric severity, overall window severity, and alert
   counts against pre-stated success criteria (control no alert,
   both drift windows alert). All criteria passed at v1.0.

## Results table

Measured 2026-11-05, simulated data only, from REPORT.md
in the repo.

| Level | Set | Headline result | Steps and cost | Tests |
| --- | --- | --- | --- | --- |
| Learn | 10 simulated requests | 22,750 tokens, cost 9.80 USD, labels 10 of 10 | Mean latency 550.0 ms, 20 spans | 21 |
| Build | 60 simulated requests | 2,208 proxy tokens, cost 1.062 USD, 180 spans | Mean latency 333.167 ms, p50 315, p95 561 | 18 (39 total) |
| Deep, control | 1,000 records vs 1,000 baseline | 0 alerts, severity none, latency PSI 0.025905 | Simulated pass 0.909 to 0.933 | 8 Deep (47 total) |
| Deep, latency and cost drift | Same window size | 3 alerts, severity high, latency PSI 8.045714, mean shift 4.480065 | Latency mean 498.367 to 853.770 ms, cost PSI 8.283089 | 8 Deep (47 total) |
| Deep, quality drift | Same window size | 1 alert, severity high | Simulated pass rate 0.909 to 0.628, drop 0.281, z -14.896831 | 8 Deep (47 total) |

## Venue class note

Per PROPOSAL.md, the paper angle for P12 is a drift detection note
(one real drift caught, or the method with a seeded drift). This
brief is the seeded-drift form, stated as such. Venue class is a
workshop or conference in ML systems or LLM operations, or a
journal of the AJSE class, per the publications pipeline tracker
rules. One venue at a time. No venue is named as submitted,
accepted, or contacted in this brief. Fees, if any, arise only
after acceptance and remain Jesun's call under the free-only rule.

## Limits the paper must carry

- Simulated data only. No real LLM, live traffic, or real drift
  was measured. Seeded separation does not prove real-world
  detection.
- Quality is a simulated boolean field. Real quality is graded,
  delayed, and often human judged.
- Build token counts are the ceil(len/4) proxy, not a tokenizer,
  and prices are stated teaching constants.
- Thresholds are documented constants, not learned or calibrated.
  PSI is bin-edge and window-size sensitive, as the recorded
  200-record failure shows.
- Cost and tokens are correlated by construction in Deep, so
  joint alerts can double-count one underlying change.
- Compressed Deep only. The v1.1 backlog (real integration, real
  tokenizer, learned thresholds, embedding drift, alert delivery,
  graded quality, seasonality handling) is future work, named in
  PROPOSAL.md in the repo.

## Submission gate

Submission is Jesun's tap and nothing is submitted. This brief is
the candidate only.
