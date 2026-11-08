# Watching the Machine Think: Building llm-observability in the Open

By Jesun Ahmad Ushno
Date: 2026-11-05
Status: DRAFT, written fan-out for P12 llm-observability v1.0. Not posted.

## The problem

An LLM call that is not logged cannot be priced, traced, or
trusted. When latency rises, cost creeps, or answer quality drops,
a team without request logs, traces, and version records is left
guessing which prompt, which model, and which change caused it.
This project builds that observability layer in the open, small
enough to read and check by hand.

This project, P12 in Roadmap v3, builds LLM observability in three
levels: request logging, tracing, and a version registry; then a
persistent service with a registry diff and a static dashboard;
then drift detection and alerts over logged windows. All code runs
with the Python standard library only. Every request is simulated.
No real LLM was called at any level, and nothing here claims
otherwise. Quality in Deep is a simulated logged field, never real
model quality.

Repository: https://github.com/JesunAhmadUshno/llm-observability

## Past, present, future (the dossier, condensed)

Past: general observability stacks in the Langfuse class already
exist. The prior art and the problem history are recorded in
PROPOSAL.md in the repo. The novelty claim there
stays marked PROPOSED. This post makes no novelty claim beyond the
measured work below.

Present: v1.0 closes three levels on 2026-11-05. Learn built
request logging, tracing spans, and a prompt and model version
registry on 10 simulated requests. Build
added a persistent JSONL store, a simulated service with nested
spans, a registry diff, and a static dashboard over 60 simulated
requests. Compressed Deep added drift
detection (PSI, mean shift, and a two-proportion z check) and
alerts over seeded windows of 1,000 records each.

Future: the rest of the v2 Deep scope is named in PROPOSAL.md in
the repo (next cycle). It includes real LLM integration,
a real tokenizer, learned thresholds, embedding drift, alert
delivery channels, graded quality signals, seasonality handling,
and persistence for drift reports. None of that is done, and none
of it is claimed here.

## Main results claim

At v1.0, on simulated data only with no real LLM called: Learn passed 21 tests on 10 simulated requests, recording 22,750 total tokens (15,500 prompt plus 7,250 completion) at a total cost of 9.80 USD from the stated teaching price table, with mean latency 550.0 ms, p50 500 ms, p95 1000 ms, 20 trace spans, and cost labels matched on 10 of 10 requests; Build passed 18 tests (39 tests in total) on 60 simulated requests persisted and reloaded with 180 trace spans, totalling 2,208 proxy tokens (876 prompt plus 1,332 completion, proxy ceil(len/4), not a real tokenizer) at a total cost of 1.062 USD, with mean latency 333.167 ms, p50 315 ms, p95 561 ms, and a registry diff for prompt v1 to v2 that added "Cite the source line." with no lines removed and 2 lines unchanged; compressed Deep passed 8 tests (47 tests in total) with a drift detector (PSI, mean shift in pooled SD units, and a two-proportion z check on a simulated quality field) over windows of 1,000 records each, where the control window raised 0 alerts at severity none with latency PSI 0.025905, the latency and cost drift window raised 3 alerts at severity high with latency PSI 8.045714, latency mean shift 4.480065, and latency mean 498.367 to 853.770 ms, and the quality drift window raised 1 alert at severity high with the simulated pass rate falling from 0.909 to 0.628, a drop of 0.281.

Every number in that claim comes from a run recorded in
REPORT.md and results files in the repo, on simulated data. Read the
limits section below before quoting any of it.

## Results by level

### Level 1, Learn (release v0.1)

Learn logs one structured record per request: prompt, prompt hash,
model, prompt and completion tokens, total tokens, cost, latency,
and the prompt and model versions in use. Cost is (prompt tokens
/ 1000) times the input rate plus (completion tokens / 1000) times
the output rate, from a stated teaching price table (alpha-small
input 0.10, output 0.20; alpha-large input 0.50, output 1.00, in
dollars per 1,000 tokens). The tracer creates nested spans read
from an injected clock, so durations are deterministic. The
registry registers prompt and model versions, rejects duplicates,
and keeps a changelog.

| Measure | Result |
| --- | --- |
| Simulated requests | 10 |
| Total tokens | 22,750 (15,500 prompt plus 7,250 completion) |
| Total cost USD (stated price table) | 9.80 |
| Mean latency ms | 550.0 |
| p50 / p95 latency ms | 500 / 1000 |
| Per-model cost USD | alpha-small 1.30 (6 requests), alpha-large 8.50 (4 requests) |
| Trace spans | 20 (10 roots, 10 model_call children) |
| Cost labels matched | 10 of 10 |
| Tests | 21 |
| Determinism | results_learn.json identical across two runs (hash verified) |

### Level 2, Build (release v0.5)

Build persists records and spans to one JSONL store, serves 60
simulated requests through nested spans (a root request span plus
prepare and model_call children), diffs registry versions line by
line, and generates a static HTML dashboard from the stored
records. Token counts use the stated proxy ceil(len(text) / 4),
not a real tokenizer.

| Measure | Result |
| --- | --- |
| Simulated requests served and persisted | 60 |
| Total tokens (proxy) | 2,208 (876 prompt plus 1,332 completion) |
| Total cost USD (stated price table) | 1.062 |
| Mean latency ms | 333.167 |
| p50 / p95 latency ms | 315 / 561 |
| Per-model cost USD | alpha-small 0.177 (30 requests), alpha-large 0.885 (30 requests) |
| Trace spans | 180 (60 roots, 120 children) |
| Registry diff prompt v1 to v2 | added: Cite the source line.; removed: none; unchanged: 2 lines |
| Corrupt lines on reload | 0 |
| Tests | 18 Build, 39 in total |
| Determinism | results_build.json identical across two runs except benchmark_reload_aggregate_ms, the named timing field |

### Level 3, Deep, compressed (release v1.0)

Deep compares a baseline window against a current window on
latency, total tokens, cost, and the simulated quality pass rate.
Numeric metrics use PSI on baseline quantile bins and mean shift
in pooled standard deviation units. Quality uses a two-proportion
z check: an alert requires a drop of at least 0.10 and absolute z
at least 1.96. Each window holds 1,000 records. Window size was
raised from 200 to 1,000 after the first run showed PSI sampling
noise firing medium alerts on the control at 200; that change and
its reason are recorded in REPORT.md, not hidden.

| Window | Overall severity | Alerts | Headline numbers |
| --- | --- | --- | --- |
| control_no_drift | none | 0 | latency PSI 0.025905, tokens PSI 0.009285, cost PSI 0.009807, simulated pass 0.909 to 0.933 |
| latency_cost_drift | high | 3 | latency PSI 8.045714 (mean 498.367 to 853.770, mean shift 4.480065), cost PSI 8.283089, tokens PSI 4.427765 |
| quality_drift | high | 1 | simulated pass rate 0.909 to 0.628, drop 0.281, z -14.896831; other metrics severity none |

Tests: 8 Deep tests, 47 in total with Learn and Build.
Determinism: results_deep.json identical across two runs, with no
timing field.

## Honest limits

- Simulated only, at every level. No real LLM was called, no live
  traffic was measured, and no network service runs.
- Token counts differ by level by design: Learn uses fixed token
  fields in a labelled dataset, and Build uses the proxy
  ceil(len(text) / 4), which is a rule of thumb, not a real
  tokenizer. Real token counts differ by model and by text.
- The price table holds stated teaching constants, not live vendor
  prices. Costs are arithmetic on those constants.
- Quality in Deep is a simulated boolean logged field
  (quality_pass). A pass-rate drop in real traffic can reflect
  labelling delay, not model change.
- Drift thresholds are documented constants (PSI warning 0.10,
  alert 0.25; mean shift warning 0.5, alert 1.0), not learned or
  calibrated on real data. They will be wrong for some real
  distributions.
- Cost and tokens are correlated in Deep by construction, because
  cost derives from tokens. Alerting on both can double-count one
  underlying change.
- The Build dashboard is one static HTML file. There is no live
  refresh, query API, or filtering. The JSONL store is a single
  local file with no locking, indexing, or rotation.
- Alerts in Deep are data in JSON and return values only. No
  email, webhook, or paging channel exists in v1.0.
- Compressed Deep is not the full v2 Deep scope. The remainder is
  the next cycle named in PROPOSAL.md.
- The runs executed on the Muse VM, not the assigned BlackBoxV2
  node, as REPORT.md states.

## Where to go next

- Tutorial: fanout/tutorial.md in the repo, a step-by-step module
  that runs all three levels and the full test suite.
- Releases: v0.1 (Learn), v0.5 (Build), v1.0 (Learn, Build,
  compressed Deep) on the GitHub repo linked above.
- Book chapter: "Watching The Machine Think" per PROPOSAL.md, held as
  a draft angle in this fan-out set.
- License: code Apache-2.0, tutorials CC BY 4.0.
