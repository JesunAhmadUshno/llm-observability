# SPEC: llm-observability (P12)

Phase skill: spec-driven-development (house engineering pipeline).
Status: Wave 0 scaffold spec, from Roadmap v2 text and the v3 decision pack. Scope and acceptance criteria below are the v2 section text, kept as the source of truth until the project's wave opens its own spec pass.

Fleet node: BlackBoxV2. Wave: Wave 5.
Hiring evidence: 4 of 5 (required duty at Mistral, v2 rank 9) [confirmed, fleet and scoring pass 2026-11-04, or the decision pack for P23 to P29].

## Project section text (Roadmap v2, or the v3 candidate text for P23 to P29)

llm-observability: KEEP

Subject: LLM operations (LLMOps). v1 levels carry over: log every request (prompt, model, tokens, cost, latency); a tracing dashboard and a prompt and model version registry; Deep adds quality drift detection and alerts. One scope note: the Go service the career documentation once suggested for this project moves to P21 (change 13). This project stays Python and stays about seeing the system clearly.
Fan-out: Book chapter "Watching The Machine Think". Paper angle: a drift detection note (one real drift caught, or the method with a seeded drift). Course module: P12-llm-observability.

## Acceptance criteria (scaffold level)

- Learn closes when the level-1-learn code runs, its README teaches the idea, and a fresh-eyes reader can follow it.
- Build closes when the system runs end to end, tests pass, and one benchmark or result table with method is in the README.
- Deep closes when the Deep scope in the section text is done, the failure modes are written, and the dossier is updated to ship state.
- No level closes on a claim. Evidence only: code, tests, numbers, links.
