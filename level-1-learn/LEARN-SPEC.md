# LEARN-SPEC: llm-observability (P12), Level 1 Learn

Phase skill: spec-driven-development (house engineering pipeline).
Status: written for the December Compression Protocol, Sprint 2 early
pull, 2026-11-05. This spec narrows the scaffold SPEC.md section text
to the Learn scope only.

## Scope (Learn only)

From SPEC.md: log every request (prompt, model, tokens, cost,
latency); a tracing dashboard and a prompt and model version
registry. Deep adds quality drift detection and alerts.

Learn builds the smallest honest version of the first three ideas:

1. RequestLogger: one structured record per request with prompt,
   prompt hash, model, prompt and model versions, prompt tokens,
   completion tokens, total tokens, cost, and latency.
2. Cost from a stated price table. The prices are teaching constants
   (dollars per 1,000 tokens), stated in the code and the README.
   They are not live vendor prices.
3. Tracer: spans with parent and child links and durations, driven
   by an injected clock so tests and the runner are deterministic.
4. VersionRegistry: prompt and model versions with register,
   resolve (named version or latest), list, and a changelog.
   Duplicate registration raises.
5. aggregate(): counts, token totals, total cost, mean latency, and
   nearest-rank p50 and p95 latency, overall and per model. This is
   the Learn form of the dashboard: a summary table, printed as text.
   A web dashboard is Build level scope.

## Teaching dataset

level-1-learn/requests.json: 10 labelled simulated requests over
2 models (alpha-small, alpha-large). Labelled means every request
carries its expected_cost_usd, hand-computed from the price table,
and the runner and the tests check the computed cost against it.
All data is simulated. No real LLM is called, and no request leaves
this machine.

## Out of scope at Learn

- No real LLM call, no network, no external service.
- No web dashboard, no database, no persistence beyond the results
  JSON file. Build level scope.
- No quality drift detection and no alerts. Deep level scope in
  SPEC.md.
- No live vendor prices. The price table is a teaching constant.

## Acceptance criteria

- The runner (run_learn.py) runs on Python 3.12 with the standard
  library only and writes results_learn.json.
- Two consecutive runs produce an identical results_learn.json
  (verified by sha256).
- Unit tests in tests/test_learn_observability.py pass, with
  hand-computed expected values for cost, token totals, latency
  statistics, spans, and registry behaviour.
- Every number in the level README comes from the runner output.
- The scaffold smoke test still passes.

## Fleet note

SPEC.md assigns BlackBoxV2. This level is pure CPU standard library
code and was run on the Muse VM. That is named as a grade deduction
in the level README, following the pattern of earlier Learn levels.
