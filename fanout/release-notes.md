# Release notes draft: llm-observability

Status: DRAFT notes for releases that already exist. Dated 2026-11-05.
These notes summarise the existing GitHub releases. No new release is
created by this file.

Releases verified with gh release list on 2026-11-05:
v0.1, v0.5, and v1.0, at the URLs below.

## v0.1, Learn: request logging, tracing, version registry

URL: https://github.com/JesunAhmadUshno/llm-observability/releases/tag/v0.1

- Request logging, tracing, and a prompt and model version
  registry, built with the Python standard library only. One
  structured record per request, nested trace spans from an
  injected clock, and cost from a stated teaching price table.
  Every request is simulated. No real LLM was called.
- Measured run: 10 simulated requests, 22,750 total tokens (15,500
  prompt plus 7,250 completion), total cost 9.80 USD, mean latency
  550.0 ms, p50 500 ms, p95 1000 ms, 20 trace spans, cost labels
  matched 10 of 10.
- Tests: 21 unit tests in tests/test_learn_observability.py, plus
  the scaffold smoke test.
- Limits carried in the release: simulated only, small fixed set,
  in-memory only, teaching price constants, no drift detection.

## v0.5, Build: persistent service, registry diff, dashboard

URL: https://github.com/JesunAhmadUshno/llm-observability/releases/tag/v0.5

- A persistent observability service on the Learn layer: a JSONL
  LogStore for records and spans, a simulated service with three
  nested spans per request, registry diff by line and by field,
  and a static HTML dashboard generated from stored records. Token
  counts use the stated proxy ceil(len(text) / 4), not a real
  tokenizer. No real LLM was called and no network service runs.
- Measured run: 60 simulated requests persisted and reloaded, 180
  trace spans, 2,208 proxy tokens (876 prompt plus 1,332
  completion), total cost 1.062 USD, mean latency 333.167 ms, p50
  315 ms, p95 561 ms, corrupt lines 0. Registry diff prompt v1 to
  v2: added Cite the source line., removed none, unchanged 2 lines.
- Tests: 18 Build unit tests, 39 in total with Learn.
- Limits carried in the release: simulated only, token proxy,
  static dashboard only, single-file store with no locking, no
  drift detection in this level.

## v1.0, Deep: drift detection and alerts

URL: https://github.com/JesunAhmadUshno/llm-observability/releases/tag/v1.0

- Compressed Deep under the December Compression Protocol: drift
  detection over logged windows in level-3-deep/drift.py, using
  PSI and mean shift for latency, tokens, and cost, and a
  two-proportion z check for the simulated quality pass rate.
  Quality is a simulated logged field throughout, never real model
  quality.
- Evaluation set: a seeded simulated experiment with a baseline
  window and three current windows of 1,000 records each (control
  with no drift, latency and cost drift, quality drift). Full
  results are in level-3-deep/results_deep.json, identical across
  two runs with no timing field.
- Measured run: control overall severity none with 0 alerts
  (latency PSI 0.025905); latency and cost drift overall high with
  3 alerts (latency PSI 8.045714, mean shift 4.480065, latency mean
  498.367 to 853.770 ms); quality drift overall high with 1 alert
  (simulated pass rate 0.909 to 0.628, drop 0.281, z -14.896831).
  All success criteria passed.
- Tests: 8 Deep unit tests, 47 in total with Learn and Build.
- The rest of the v2 Deep scope is the next cycle in PROPOSAL.md.
  It is not part of v1.0 and is not claimed by these notes.
