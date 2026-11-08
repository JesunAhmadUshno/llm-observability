# PROPOSAL: llm-observability (P12)

Status: NOT LOCKED. This repo is **not pre-registered**: the scaffold
spec (commit c4fc431, 2026-11-04) set scope and acceptance criteria but
no hypotheses or pass lines, and the Deep success criteria were written
in the same commit as the first Deep results (cb96c1e). Under the
portfolio standard (METHOD section 7) the repo is capped at Functional
until a confirmatory cycle runs under a newly locked proposal.

This file gathers the planning record that used to sit in SPEC.md,
level-1-learn/LEARN-SPEC.md, NOVELTY.md, DOSSIER.md and ROADMAP.md,
moved here on 2026-11-08 with the text kept.

Inside the moved sections, a mention of SPEC.md, LEARN-SPEC.md, NOVELTY.md,
DOSSIER.md or ROADMAP.md means the PROPOSAL.md section marked "was" that
file; a mention of a level README, the Deep README or the research review
means the REPORT.md section marked "was" that file.

## Question

Can request logging, tracing and a simple drift rule (PSI, pooled-SD
mean shift, two-proportion z) flag latency, cost and quality drift
between windows of logged LLM requests, and how often does that rule
false-alarm or miss on a known generator?

## Hypotheses as recorded after the fact (not pre-registered)

- H1: on a no-drift control window the detector raises no alert.
- H2: on a window with injected latency and cost drift, an alert fires.
- H3: on a window with an injected drop in the simulated pass rate,
  an alert fires.

These were the Deep success criteria, written with the results. They
are scored in REPORT.md; they do not count as a locked test.

## Next cycle: what a locked confirmatory proposal needs

To lift the cap, a new PROPOSAL revision is locked (tagged) before any
of these runs, with numeric pass lines. For the Systems, reliability
profile that means stated targets (alert delay, false-alert rate per
window), a timed drill (a planned, injected fault on a real service
caught by the monitoring), and a runbook a second person can follow.
The gaps found by the 2026-11-07 review, and what each needs:

| Gap | What it needs |
| --- | --- |
| No real traffic: every request, token, latency and quality value is simulated. | A log of real LLM calls: at least two windows of 1,000+ requests each from one service, with timestamps, model, prompt version, measured latency, provider-reported tokens and cost. Either a small paid API budget, or a local model server (CPU or one GPU) driven by a fixed prompt set. |
| Thresholds not calibrated on real data. | The same real log, split into many no-drift window pairs, to set PSI and SD thresholds for a target false-alert rate (for example 1% per window). |
| Quality is one simulated boolean. | Graded quality labels on real outputs: a labelled eval set (a few hundred prompts with reference answers or a rubric) and either human grading or a scored judge, plus the delay between output and label. |
| No output-text or embedding drift. | Real output text and an embedding model (CPU is enough for a small sentence encoder over a few thousand outputs). |
| No comparison with an existing tool. | A self-hosted Langfuse-class stack ingesting the same real log, with the same injected changes, to compare alerts and detection delay. |
| Tight intervals. | More repetitions (for example 500 per setting instead of 50): CPU only, roughly 10 times the current 4 s run, so cheap whenever needed. |
| Sequential detection delay only for latency. | Extend the CUSUM stream to tokens, cost and pass rate (CPU, seconds); with real data, measure delay on a timestamped incident. |
| No literature review. | A dated review of drift-detection and LLM-observability sources, written into `DOSSIER.md` with links. Reading time only. |

## Scaffold spec (was SPEC.md)

Phase skill: spec-driven-development (house engineering pipeline).
Status: Wave 0 scaffold spec, from Roadmap v2 text and the v3 decision pack. Scope and acceptance criteria below are the v2 section text, kept as the source of truth until the project's wave opens its own spec pass.

Fleet node: BlackBoxV2. Wave: Wave 5.
Hiring evidence: 4 of 5 (required duty at Mistral, v2 rank 9) [confirmed, fleet and scoring pass 2026-11-04, or the decision pack for P23 to P29].

### Project section text (Roadmap v2, or the v3 candidate text for P23 to P29)

llm-observability: KEEP

Subject: LLM operations (LLMOps). v1 levels carry over: log every request (prompt, model, tokens, cost, latency); a tracing dashboard and a prompt and model version registry; Deep adds quality drift detection and alerts. One scope note: the Go service the career documentation once suggested for this project moves to P21 (change 13). This project stays Python and stays about seeing the system clearly.
Fan-out: Book chapter "Watching The Machine Think". Paper angle: a drift detection note (one real drift caught, or the method with a seeded drift). Course module: P12-llm-observability.

### Acceptance criteria (scaffold level)

- Learn closes when the level-1-learn code runs, its README teaches the idea, and a fresh-eyes reader can follow it.
- Build closes when the system runs end to end, tests pass, and one benchmark or result table with method is in the README.
- Deep closes when the Deep scope in the section text is done, the failure modes are written, and the dossier is updated to ship state.
- No level closes on a claim. Evidence only: code, tests, numbers, links.

## Learn spec (was level-1-learn/LEARN-SPEC.md)

Phase skill: spec-driven-development (house engineering pipeline).
Status: written for the December Compression Protocol, Sprint 2 early
pull, 2026-11-05. This spec narrows the scaffold SPEC.md section text
to the Learn scope only.

### Scope (Learn only)

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

### Teaching dataset

level-1-learn/requests.json: 10 labelled simulated requests over
2 models (alpha-small, alpha-large). Labelled means every request
carries its expected_cost_usd, hand-computed from the price table,
and the runner and the tests check the computed cost against it.
All data is simulated. No real LLM is called, and no request leaves
this machine.

### Out of scope at Learn

- No real LLM call, no network, no external service.
- No web dashboard, no database, no persistence beyond the results
  JSON file. Build level scope.
- No quality drift detection and no alerts. Deep level scope in
  SPEC.md.
- No live vendor prices. The price table is a teaching constant.

### Acceptance criteria

- The runner (run_learn.py) runs on Python 3.12 with the standard
  library only and writes results_learn.json.
- Two consecutive runs produce an identical results_learn.json
  (verified by sha256).
- Unit tests in tests/test_learn_observability.py pass, with
  hand-computed expected values for cost, token totals, latency
  statistics, spans, and registry behaviour.
- Every number in the level README comes from the runner output.
- The scaffold smoke test still passes.

### Fleet note

SPEC.md assigns BlackBoxV2. This level is pure CPU standard library
code and was run on the Muse VM. That is stated as a limit
in REPORT.md.

## Prior work and novelty (was NOVELTY.md)

Status: DRAFT, PROPOSED. Not verified. This text does not move into any public post, paper, or profile until the Jev claim_check gate passes on the exact text.

### Proposed claim

Against general observability stacks (Langfuse class): this project aims to differ in the way its SPEC.md section text defines (a from-zero or self-hosted build, measured in public, on a named home fleet, with the failure modes written down). The exact difference is stated at the project's wave, after the prior art is re-read.

### Prior art table

| Prior art | What it does | What this project does differently | Measured difference |
| --- | --- | --- | --- |
| general observability stacks (Langfuse class) | See DOSSIER.md, Past | PROPOSED, see the claim above | NO MEASUREMENT YET |

### Honest size

If the novelty proves small, this file will say so and name the real value instead (a cleaner reproduction, a better benchmark, a first public dataset). No novelty is invented to fill this section.

## Dossier: past, present, future (was DOSSIER.md)

Written under the documentation and publishing standard (past, present, future). Updated at ship time.

### Past

Prior art for this project is named in NOVELTY.md (general observability stacks (Langfuse class)). The history of the problem, the key papers and systems, and what was tried before are recorded in the Roadmap v2 section text in SPEC.md and will be expanded with dated sources at the project's wave, before Build opens.

### Present

Current demand evidence: hiring value 4 of 5 (required duty at Mistral, v2 rank 9) [confirmed, fleet and scoring pass 2026-11-04; for P23 to P29, the decision pack 2026-11-04]. The Round 3 research (2026-11-04) found the market centre at post-training, evals, environments, and inference depth [confirmed as the research finding; the report is at ~/workspace/research_notes/roadmap-v3-revaluation-research-20261104-0949/report.md]. Tools and versions are pinned at Build time, not in this v1.

### Ship note (2026-11-05)

Level 1 Learn shipped as v0.1 under the December Compression Protocol (Sprint 2 early pull): request logging, tracing spans, and a prompt and model version registry, standard library only, on 10 labelled simulated requests. Measured results are in REPORT.md. Level 2 Build shipped as v0.5 (2026-11-05): a persistent JSONL LogStore, an ObservabilityService with nested spans over 60 simulated requests, registry diff, and a static HTML dashboard, standard library only; results in REPORT.md. Deep is not started.

### Ship note: Deep v1.0 (2026-11-05)

Level 3 Deep shipped as v1.0 under the December Compression Protocol (Sprint 2 early pull): drift detection in level-3-deep/drift.py (PSI, mean shift in pooled SD units, two-proportion z for the simulated pass rate) and a seeded simulated experiment in run_deep.py with baseline, no-drift control, latency-and-cost drift, and quality drift windows of 1000 records each. Measured: control overall none with 0 alerts, latency-cost drift overall high with 3 alerts, quality drift overall high with 1 alert (simulated pass rate 0.909 to 0.628, drop 0.281, z -14.896831). Quality is a simulated logged field throughout, never real model quality. Tests 47 passed. Results in REPORT.md. The rest of Deep scope is the v1.1 backlog below.

### Future

Open problems and the project's next steps sit in the Deep level scope in SPEC.md. Any forecast about this field is [unverified] unless a dated primary source is added here at the wave update.

## v1.1 backlog (was ROADMAP.md)

Status after v1.0 (2026-11-05): Learn, Build, and compressed Deep are done. The items below are the rest of the Deep scope, held for v1.1, not claimed in v1.0.

### v1.1 backlog

- Real LLM or live service integration: run drift detection on logs from a real model endpoint, with consent, rate limits, and cost controls named first.
- Real tokenizer: replace token proxies and simulated token fields with a real tokenizer count per model.
- Learned or adaptive thresholds: calibrate PSI, mean-shift, and pass-rate thresholds on held-out real windows instead of documented constants.
- Embedding or output-text drift: add drift scores over output text or embeddings, with a stated distance and binning method.
- Alert delivery channels: webhook, email, or dashboard alert delivery with acknowledgement and dedup, not JSON-only alerts.
- Larger and graded quality signals: replace the simulated boolean quality_pass with graded, delayed, human or judge based quality where available, labelled by source.
- Seasonality and model-mix handling: stratify windows by model, prompt version, and time of day before scoring drift.
- Persistence for drift reports: store drift reports alongside the Build JSONL store and show them on the dashboard.
