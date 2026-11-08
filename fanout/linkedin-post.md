# LinkedIn post draft: P12 llm-observability v1.0

Status: DRAFT NOT POSTED
Date drafted: 2026-11-05
Author: Jesun Ahmad Ushno
Rule for this platform: the link goes in the first comment, not in the
post body. The first comment line is at the end of this file.

## Post body

An LLM call you do not log is a call you cannot price, trace, or
trust. So I built the observability layer in the open, and labelled
every simulated number as simulated.

llm-observability v1.0 is done: Learn, Build, and a compressed
Deep, Python standard library only. No real LLM was called at any
level.

Learn: request logging, nested tracing spans, and a prompt and
model version registry. On 10 simulated requests: 22,750 total
tokens, cost 9.80 USD from a stated teaching price table, mean
latency 550.0 ms, 20 spans, cost labels matched 10 of 10. 21 tests.

Build: a persistent JSONL store, a simulated service with three
spans per request, a registry diff, and a static dashboard. On 60
simulated requests: 2,208 proxy tokens (ceil(len/4), not a real
tokenizer), cost 1.062 USD, mean latency 333.167 ms, p50 315, p95
561, 180 spans. The prompt v1 to v2 diff added one line: Cite the
source line. 39 tests in total.

Deep (compressed): drift detection with PSI, mean shift, and a
two-proportion z check over windows of 1,000 records. Control:
0 alerts, severity none, latency PSI 0.025905. Latency and cost
drift: 3 alerts, severity high, latency PSI 8.045714, mean shift
4.480065, latency mean 498.367 to 853.770 ms. Quality drift:
1 alert, severity high, simulated pass rate 0.909 to 0.628, drop
0.281. 47 tests in total, with the limits
named in the repo.

The honest limits, in the post and not in a footnote: simulated
data only; Build tokens are a stated proxy; prices are teaching
constants, not vendor prices; Deep quality is a simulated boolean
field, not real model quality; and drift thresholds are documented
constants, not learned values. The rest of the Deep scope is named
as the v1.1 backlog in the repo, not claimed as done.

If you run LLM systems: what is the first signal you check when
cost or latency moves, the log, the trace, or the version diff?

## First comment (post this as the first comment, per the standing rule)

Repo, releases v0.1, v0.5, and v1.0, and the full tutorial: https://github.com/JesunAhmadUshno/llm-observability
