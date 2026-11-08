# llm-observability

**Question.** Can request logging, tracing and a simple drift rule
(PSI, pooled-SD mean shift, two-proportion z) flag latency, cost and
quality drift between windows of logged LLM requests, and how often
does that rule false-alarm or miss on a known generator?

**Headline.** On simulated request logs at 1,000 records per window,
the drift rule raised no false alert in 50 no-drift control pairs
(0/50, Wilson 95% 0.00 to 0.07) and alerted on both injected drifts,
but it is weak on small changes: a 0.25 SD latency shift alerted in
15/50 runs (0.19 to 0.44) where a KS baseline caught 50/50, and below
500 records per window it false-alarmed in 38/50 to 50/50 controls.
No real LLM traffic was observed.

**Field.** Systems and infrastructure, reliability. **Job family.**
LLM operations (MLOps and platform engineering).

**Verdict.** Functional, not pre-registered. Tests pass in CI on
Python 3.11 and 3.12, the results are regenerated from the seeded
generators by one command per component and checked byte for byte in
CI, and the logger, service and detector have run end to end on
simulated traffic. No plan was locked before results, and the
reliability profile (targets, a timed drill on a real service, a
runbook) is not met, so the repo stops at Functional.

Live dashboard: https://jesunahmadushno.github.io/llm-observability/
(a drift lab and false-alarm explorer that re-run the detector in your
browser, recorded traces and a cost calculator; every number is read
from the result files at build time).

## Reproduce

```text
python3 -m unittest discover -s tests -v
python3 level-1-learn/run_learn.py
python3 level-2-build/run_build.py
python3 level-3-deep/run_deep.py
python3 level-3-deep/calibrate.py
git diff --stat
```

Python 3.11 or later, standard library only. Each runner rewrites its
committed result file; `git diff` shows nothing except the one timing
field `benchmark_reload_aggregate_ms` in results_build.json. The
calibration study takes about 4 seconds on a CPU.

## Lifecycle

- Question: DONE 2026-11-04
- Proposal: OPEN (not pre-registered; see PROPOSAL.md)
- Baseline: DONE 2026-11-05
- Build: DONE 2026-11-05
- Evaluate: OPEN
- Report: DONE 2026-11-08
- Review: OPEN
- Release: OPEN

## Layout

| Path | What it holds |
| --- | --- |
| PROPOSAL.md | Question, hypotheses as recorded, prior work, scaffold spec, and what a locked confirmatory cycle needs (not locked) |
| REPORT.md | Method, results, hypotheses scored with misses, threats, the 2026-11-07 review |
| level-1-learn/ | Code: request logger, tracer, version registry (observability.py), runner, the 10-request labelled dataset, results_learn.json |
| level-2-build/ | Code: JSONL store and service (service.py), dashboard generator, runner; evidence: store_build.jsonl, dashboard.html, results_build.json |
| level-3-deep/ | Code: drift detector (drift.py), seeded experiment (run_deep.py), calibration study (calibrate.py); results_deep.json, results_calibration.json |
| tests/ | Unit tests for every component and the layout check (tests/test_smoke.py) |
| docs/decisions/ | Records of hard-to-reverse choices |
| site/ | The live dashboard, built from the files above |
| fanout/ | Dated publicity drafts (2026-11-05) and the channel log, fanout/PUBLICITY.md |
| CHANGELOG.md, CITATION.cff, SECURITY.md, LICENSE | Release history, citation, security policy, licence |

No experiments/ or results/ folder: all evidence is generated from
fixed seeds, so each result file sits next to the code that writes it
and CI proves it regenerates unchanged (decision 0002).

## License

Code: Apache-2.0 (see LICENSE). Tutorials: CC BY 4.0. Ruled in D-V3-11, 2026-11-04.
