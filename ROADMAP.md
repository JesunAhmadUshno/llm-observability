# ROADMAP: llm-observability v1.1 backlog

Status after v1.0 (2026-11-05): Learn, Build, and compressed Deep are done. The items below are the rest of the Deep scope, held for v1.1, not claimed in v1.0.

## v1.1 backlog

- Real LLM or live service integration: run drift detection on logs from a real model endpoint, with consent, rate limits, and cost controls named first.
- Real tokenizer: replace token proxies and simulated token fields with a real tokenizer count per model.
- Learned or adaptive thresholds: calibrate PSI, mean-shift, and pass-rate thresholds on held-out real windows instead of documented constants.
- Embedding or output-text drift: add drift scores over output text or embeddings, with a stated distance and binning method.
- Alert delivery channels: webhook, email, or dashboard alert delivery with acknowledgement and dedup, not JSON-only alerts.
- Larger and graded quality signals: replace the simulated boolean quality_pass with graded, delayed, human or judge based quality where available, labelled by source.
- Seasonality and model-mix handling: stratify windows by model, prompt version, and time of day before scoring drift.
- Persistence for drift reports: store drift reports alongside the Build JSONL store and show them on the dashboard.
