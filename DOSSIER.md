# DOSSIER: llm-observability (P12) v1, 2026-11-04

Written under the documentation and publishing standard (past, present, future). Updated at ship time.

## Past

Prior art for this project is named in NOVELTY.md (general observability stacks (Langfuse class)). The history of the problem, the key papers and systems, and what was tried before are recorded in the Roadmap v2 section text in SPEC.md and will be expanded with dated sources at the project's wave, before Build opens.

## Present

Current demand evidence: hiring value 4 of 5 (required duty at Mistral, v2 rank 9) [confirmed, fleet and scoring pass 2026-11-04; for P23 to P29, the decision pack 2026-11-04]. The Round 3 research (2026-11-04) found the market centre at post-training, evals, environments, and inference depth [confirmed as the research finding; the report is at ~/workspace/research_notes/roadmap-v3-revaluation-research-20261104-0949/report.md]. Tools and versions are pinned at Build time, not in this v1.

## Ship note (2026-11-05)

Level 1 Learn shipped as v0.1 under the December Compression Protocol (Sprint 2 early pull): request logging, tracing spans, and a prompt and model version registry, standard library only, on 10 labelled simulated requests. Measured results and the grade (8,700 of 10,000) are in level-1-learn/README.md. Level 2 Build shipped as v0.5 (2026-11-05): a persistent JSONL LogStore, an ObservabilityService with nested spans over 60 simulated requests, registry diff, and a static HTML dashboard, standard library only, grade 8,700 of 10,000 in level-2-build/README.md. Deep is not started.

## Future

Open problems and the project's next steps sit in the Deep level scope in SPEC.md. Any forecast about this field is [unverified] unless a dated primary source is added here at the wave update.
