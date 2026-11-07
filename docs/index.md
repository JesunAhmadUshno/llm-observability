# llm-observability

LLM operations: request logging, tracing, a version registry, drift detection and alerts. Built in levels with measured results at each level. All requests are simulated and labelled as simulated; no real LLM was called.

- Learn: request logging, tracing spans, and a prompt and model version registry, standard library only. On 10 simulated requests the logger recorded 22,750 total tokens at a total cost of 9.80 USD from the stated teaching price table, mean latency 550.0 ms, 20 trace spans, 21 unit tests passing.
- Build: a persistent JSONL store, a simulated service with nested spans, registry diff, and a static dashboard over 60 simulated requests. The service persisted 60 records and 180 trace spans, 2,208 proxy tokens at a total cost of 1.062 USD, mean latency 333.167 ms, 39 unit tests passing in total.
- Deep: quality drift detection and alerts over seeded simulated windows. On 1,000-record windows the detector raised no alerts on the no-drift control and caught both injected drifts. A calibration study over 50 seed pairs per setting measures false alerts by window size and detection power. Details in level-3-deep/README.md.

Grades on record (of 10,000): Learn 8,700, Build 8,700, Deep 8,500.

Every number above is already published in this repo (README.md and the level write-ups) and reproduced by the runners in this repo, checked in CI. The full write-ups are in the level folders: level-1-learn, level-2-build, level-3-deep.

Releases: https://github.com/JesunAhmadUshno/llm-observability/releases

Live dashboard (interactive, built from the same files): https://jesunahmadushno.github.io/llm-observability/
