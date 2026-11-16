"""Run the Build service over a deterministic simulated set.

Run: python level-2-build/run_build.py
Writes level-2-build/results_build.json, level-2-build/store_build.jsonl,
and level-2-build/dashboard.html.

Determinism: prompts, models, prompt versions, completion texts, and
latencies are all generated from fixed tables and the request index.
No randomness, no wall-clock timestamps in results_build.json except
the explicitly named timing field benchmark_reload_aggregate_ms,
which is measured on the host and is not part of any determinism
claim. Two runs produce identical results_build.json except that
timing field.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "level-1-learn"))

from observability import ManualClock, VersionRegistry, aggregate  # noqa: E402
from service import LogStore, ObservabilityService, registry_diff  # noqa: E402

PROMPTS = [
    "Explain photosynthesis in one paragraph for a student.",
    "Summarize the quarterly report and list three risks.",
    "Write a short product description for a steel water bottle.",
    "Translate the meeting notes into clear action items please.",
    "Draft an email asking for a deadline extension politely today.",
]

COMPLETIONS = [
    "Photosynthesis converts sunlight water and carbon dioxide into oxygen and energy in plants.",
    "The report shows growth slowed, costs rose, and hiring paused in two teams this quarter.",
    "This steel bottle keeps drinks cold for hours, fits a bike holder, and will not leak.",
    "Action items: send the draft, book the review, and confirm the budget by Friday noon.",
    "Hello, I am writing to request a short extension so the final work can be checked well.",
]

MODELS = ["alpha-small", "alpha-large"]
PROMPT_VERSIONS = ["v1", "v2"]


def build_registry():
    reg = VersionRegistry()
    reg.register("prompt", "chat-prompt", "v1",
                 "Answer briefly.\nUse plain language.")
    reg.register("prompt", "chat-prompt", "v2",
                 "Answer briefly.\nCite the source line.\nUse plain language.")
    reg.register("model", "alpha-small", "v1", "alpha-small 2026-01")
    reg.register("model", "alpha-large", "v1", "alpha-large 2026-01")
    return reg


def generate_requests(count=60):
    """Deterministic request specs for count requests."""
    specs = []
    for i in range(count):
        model = MODELS[i % 2]
        prompt_version = PROMPT_VERSIONS[(i // 10) % 2]
        prompt = PROMPTS[i % len(PROMPTS)]
        completion = COMPLETIONS[i % len(COMPLETIONS)]
        if model == "alpha-small":
            latency = 100 + ((i * 37) % 300)
        else:
            latency = 200 + ((i * 53) % 400)
        specs.append({
            "request_id": "B%02d" % (i + 1),
            "prompt": prompt,
            "model": model,
            "prompt_version": prompt_version,
            "model_version": "v1",
            "completion_text": completion,
            "simulated_latency_ms": latency,
        })
    return specs


def main():
    store_path = os.path.join(HERE, "store_build.jsonl")
    if os.path.exists(store_path):
        os.remove(store_path)
    registry = build_registry()
    clock = ManualClock()
    store = LogStore(store_path)
    service = ObservabilityService(store=store, registry=registry, clock=clock)
    specs = generate_requests(60)
    for spec in specs:
        service.handle_request(**spec)
    # Reload from disk: this is the persistence proof.
    records, spans, corrupt = store.load_all()
    # Benchmark: reload plus aggregate, measured on this host.
    start = time.perf_counter()
    bench_records, bench_spans, _ = store.load_all()
    bench_summary = aggregate(bench_records)
    _ = bench_spans
    elapsed_ms = round((time.perf_counter() - start) * 1000.0, 3)
    summary = aggregate(records)
    assert bench_summary == summary
    diff = registry_diff(registry, "prompt", "chat-prompt", "v1", "v2")
    # Dashboard from reloaded records.
    dashboard_path = os.path.join(HERE, "dashboard.html")
    from service import generate_dashboard
    generate_dashboard(records, spans, output_path=dashboard_path)
    out = {
        "label": "simulated requests only, no real LLM call, token counts are a proxy not a real tokenizer",
        "token_proxy": "ceil(len(text) / 4), minimum 1 for non-empty text, 0 for empty text",
        "summary": summary,
        "span_count": len(spans),
        "root_span_count": len([s for s in spans if s["parent_id"] is None]),
        "spans_per_request": len(spans) // len(records) if records else 0,
        "corrupt_lines": corrupt,
        "registry_diff_prompt_v1_v2": diff,
        "registry_changelog": registry.changelog(),
        "records": [
            {k: v for k, v in r.items() if k != "spans"} for r in records
        ],
        "benchmark_reload_aggregate_ms": elapsed_ms,
        "benchmark_label": "measured on whichever machine last ran run_build.py (2.341 ms on the Muse VM, 2026-11-05), reload plus aggregate over persisted records, indicative only, not part of any determinism claim",  # noqa: E501
        "dashboard_file": "dashboard.html",
        "store_file": "store_build.jsonl",
    }
    path = os.path.join(HERE, "results_build.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    print("Simulated requests:", summary["count"])
    print("Total tokens:", summary["total_tokens"],
          "(prompt", summary["prompt_tokens"],
          "+ completion", summary["completion_tokens"], ")")
    print("Total cost USD:", summary["total_cost_usd"])
    print("Mean latency ms:", summary["mean_latency_ms"],
          "p50:", summary["p50_latency_ms"],
          "p95:", summary["p95_latency_ms"])
    print("Spans:", len(spans))
    print("Corrupt lines:", corrupt)
    print("Benchmark reload+aggregate ms:", elapsed_ms)
    print("Wrote", path)
    print("Wrote", dashboard_path)
    print("Wrote", store_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
