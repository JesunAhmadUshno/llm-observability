# llm-observability

LLM operations: request logging, tracing, a version registry, drift detection and alerts.

Status: Learn DONE, Build DONE, and Deep DONE (2026-11-05, ROADMAP-V3-BATCH, v1.0). Level 1 is built, tested, and measured below: on 10 simulated requests the logger recorded 22,750 total tokens at a total cost of 9.80 USD from the stated teaching price table, mean latency 550.0 ms, 20 trace spans, 21 unit tests passing. No real LLM was called. Build adds a persistent JSONL store, a simulated service with nested spans, registry diff, and a static dashboard over 60 simulated requests (details below). Deep adds quality drift detection and alerts over seeded simulated windows (details below). Quality in Deep is a simulated logged field, never real model quality.
Project: P12. Fleet node: BlackBoxV2. Wave: Wave 5. All levels were run on the Muse VM (CPU), not BlackBoxV2; see the level READMEs for the named deduction.

## Start here

1. Read SPEC.md for scope and acceptance criteria.
2. Read DOSSIER.md for the past, present, and future of this problem (v1).
3. Read NOVELTY.md for the proposed novelty (DRAFT, pending the Jev claim_check gate).
4. Start at level-1-learn/README.md, then level-2-build, then level-3-deep.

## Level map

- Level 1, Learn: the core idea, built small and clean, with a teaching path.
- Level 2, Build: a real working system other people can run.
- Level 3, Deep: benchmarks, optimization, evaluation, hard cases.

## Benchmarks

Measured 2026-11-05 with level-1-learn/run_learn.py on the Muse VM, Python 3.12. All requests are simulated and labelled as simulated; the price table holds stated teaching constants, not live vendor prices.

| Test | Result |
| --- | --- |
| Simulated requests logged | 10 |
| Total tokens | 22,750 (15,500 prompt plus 7,250 completion) |
| Total cost USD (stated price table) | 9.80 |
| Mean latency ms | 550.0 |
| p50 latency ms | 500 |
| p95 latency ms | 1000 |
| Per-model cost USD | alpha-small 1.30 (6 requests), alpha-large 8.50 (4 requests) |
| Trace spans | 20 (10 roots, 10 model_call children) |
| Unit tests | 21 passed |
| Determinism | results_learn.json identical across two runs (hash verified) |
| Learn grade | 8,700 of 10,000 (deductions in the level README) |

## Build results

Measured 2026-11-05 with level-2-build/run_build.py on the Muse VM, Python 3.12. All requests are simulated; token counts use the stated proxy ceil(len(text) / 4), not a real tokenizer; the price table holds stated teaching constants, not live vendor prices.

| Test | Result |
| --- | --- |
| Simulated requests served and persisted | 60 |
| Total tokens (proxy) | 2,208 (876 prompt plus 1,332 completion) |
| Total cost USD (stated price table) | 1.062 |
| Mean latency ms | 333.167 |
| p50 latency ms | 315 |
| p95 latency ms | 561 |
| Per-model cost USD | alpha-small 0.177 (30 requests), alpha-large 0.885 (30 requests) |
| Trace spans | 180 (60 roots, 120 children) |
| Registry diff prompt v1 to v2 | added: Cite the source line.; removed: none; unchanged: 2 lines |
| Unit tests | 39 passed (21 Learn plus 18 Build) |
| Determinism | results_build.json identical across two runs except benchmark_reload_aggregate_ms, the named timing field |
| Build grade | 8,700 of 10,000 (deductions in the level README) |

## Deep results

Measured 2026-11-05 with level-3-deep/run_deep.py on the Muse VM, Python 3.12. All windows are seeded and simulated, 1000 records each. Quality is a simulated logged field (quality_pass), labelled simulated, not real model quality. Statistics: PSI on binned distributions, mean shift in pooled SD units, and a two-proportion z check for pass rate.

| Window | Overall severity | Alerts | Headline numbers |
| --- | --- | --- | --- |
| control_no_drift | none | 0 | latency PSI 0.025905, tokens PSI 0.009285, cost PSI 0.009807, simulated pass 0.909 to 0.933 |
| latency_cost_drift | high | 3 | latency PSI 8.045714 (mean 498.367 to 853.770), cost PSI 8.283089 (mean 0.900578 to 1.972592), tokens PSI 4.427765 |
| quality_drift | high | 1 | simulated pass rate 0.909 to 0.628, drop 0.281, z -14.896831; other metrics severity none |

| Test | Result |
| --- | --- |
| Success criteria | all passed (control no alert, both drift windows alert) |
| Unit tests | 47 passed (39 prior plus 8 Deep) |
| Determinism | results_deep.json identical across two runs, no timing field |
| Deep grade | 8,500 of 10,000 (deductions in level-3-deep/README.md) |

## Novelty

PROPOSED. See NOVELTY.md. The novelty text is a draft until the Jev claim_check gate passes on it.

## Fan-out

Written fan-out set for v1.0, dated 2026-11-05, in fanout/:

- fanout/blog-post.md: "Watching the Machine Think", the full
  story with the main results claim gated by Jev claim_check
  (model jev-1.13.0, noul 0.78, route REVIEW, no block).
- fanout/tutorial.md: course module P12-llm-observability. Every
  command in it was executed and passed on 2026-11-05 (all three
  runners, all per-level tests, full suite at 47 tests).
- fanout/website-page.md: project page copy only, not published.
- fanout/linkedin-post.md: DRAFT NOT POSTED, link as the
  first-comment line per the LinkedIn rule.
- fanout/paper-candidate.md: drift detection note at CANDIDATE.
  Submission is Jesun's tap, nothing submitted.
- fanout/release-notes.md: draft notes for the live releases
  v0.1, v0.5, and v1.0.

Publicity grades and the channel log are in PUBLICITY.md. Overall
fan-out grade: 9,533 of 10,000. The loop never posts to social:
all social channels are held with named reasons in PUBLICITY.md.

## License

Code: Apache-2.0 (see LICENSE). Tutorials: CC BY 4.0. Ruled in D-V3-11, 2026-11-04.
