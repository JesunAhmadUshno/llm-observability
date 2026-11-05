# Website project page copy: llm-observability

Site: jesunahmadushno.com
Status: COPY ONLY, draft for the project page. Dated 2026-11-05.
Nothing on any website was changed by this file.

## Headline

llm-observability: request logging, tracing, a version registry, drift detection and alerts, built in the open

## Summary

llm-observability is an open LLM operations project built by Jesun
Ahmad Ushno as project P12 in Roadmap v3. It builds the
observability stack in three levels: request logging with cost
from a stated price table, nested tracing spans, and a prompt and
model version registry; a persistent JSONL service with a registry
diff and a static tracing dashboard; and drift detection with PSI,
mean shift, and a two-proportion z check, with alerts over logged
windows. It runs on the Python standard library only. Every request
is simulated. No real LLM was called, and quality in Deep is a
simulated logged field, never real model quality.

Status: v1.0, 2026-11-05. Learn, Build, and compressed Deep are
done. Total tests: 47, all passing at v1.0. Level grades: Learn
8,700 of 10,000, Build 8,700 of 10,000, Deep 8,500 of 10,000.

## Results

All results below are measured runs on simulated data, recorded in
the level READMEs in the GitHub repo. They prove the logging,
tracing, registry, persistence, and drift machinery, not
production quality.

| Level | Set | Headline result | Notes |
| --- | --- | --- | --- |
| Learn | 10 simulated requests | 22,750 total tokens, cost 9.80 USD, labels matched 10 of 10 | Mean latency 550.0 ms, p50 500, p95 1000, 20 spans; 21 tests |
| Build | 60 simulated requests | 2,208 proxy tokens, cost 1.062 USD, 180 spans persisted | Mean latency 333.167 ms, p50 315, p95 561; registry diff added "Cite the source line."; 18 tests, 39 total |
| Deep (compressed) | 3 windows of 1,000 records each, against a 1,000 record baseline | Control 0 alerts severity none; latency and cost drift 3 alerts severity high; quality drift 1 alert severity high | Latency PSI 0.025905 control and 8.045714 drift; simulated pass rate 0.909 to 0.628, drop 0.281; 8 tests, 47 total |

## Honest limits

- Simulated data only, at every level. No real LLM was called and
  no live traffic was measured.
- Build token counts are the proxy ceil(len(text) / 4), not a real
  tokenizer. The price table is stated teaching constants, not
  live vendor prices.
- Deep quality is a simulated boolean field. Drift thresholds are
  documented constants, not learned or calibrated values.
- Compressed Deep is not the full v2 Deep scope. The remainder is
  the v1.1 backlog in the repo ROADMAP.md.

## Links

- GitHub repo: https://github.com/JesunAhmadUshno/llm-observability
- Release v0.1 (Learn): https://github.com/JesunAhmadUshno/llm-observability/releases/tag/v0.1
- Release v0.5 (Build): https://github.com/JesunAhmadUshno/llm-observability/releases/tag/v0.5
- Release v1.0 (Learn, Build, compressed Deep): https://github.com/JesunAhmadUshno/llm-observability/releases/tag/v1.0
- Tutorial: fanout/tutorial.md in the GitHub repo
- Blog post draft: fanout/blog-post.md in the GitHub repo

## License note

Code: Apache-2.0. Tutorials: CC BY 4.0.
