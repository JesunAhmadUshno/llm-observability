"""Run the Learn simulation and write deterministic results.

Run: python level-1-learn/run_learn.py
Writes level-1-learn/results_learn.json. No timestamps, no randomness,
no real LLM call: every request in requests.json is simulated and
labelled as simulated. Two runs produce an identical file.

The dataset (requests.json) is labelled: each request carries its
expected_cost_usd, hand-computed from the price table in
observability.py. The runner checks every computed cost against its
label and reports how many matched.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from observability import ManualClock, RequestLogger, Tracer, VersionRegistry, aggregate, compute_cost  # noqa: E402


def load_requests():
    with open(os.path.join(HERE, "requests.json"), encoding="utf-8") as f:
        return json.load(f)


def build_registry():
    reg = VersionRegistry()
    reg.register("prompt", "chat-prompt", "v1", "Answer briefly.")
    reg.register("prompt", "chat-prompt", "v2",
                 "Answer briefly. Cite the source line.")
    reg.register("model", "alpha-small", "v1", "alpha-small 2026-01")
    reg.register("model", "alpha-large", "v1", "alpha-large 2026-01")
    return reg


def main():
    requests = load_requests()
    registry = build_registry()
    logger = RequestLogger()
    clock = ManualClock()
    tracer = Tracer(clock.now)
    cost_matched = 0
    for req in requests:
        # Resolve the exact versions this request claims to use.
        registry.resolve("prompt", req["prompt_name"],
                         req["prompt_version"])
        registry.resolve("model", req["model"], req["model_version"])
        cost = compute_cost(req["model"], req["prompt_tokens"],
                            req["completion_tokens"])
        if cost == req["expected_cost_usd"]:
            cost_matched += 1
        latency = req["latency_ms"]
        with tracer.span("request:" + req["request_id"]):
            clock.advance(latency // 2)
            with tracer.span("model_call:" + req["model"]):
                clock.advance(latency - latency // 2)
            logger.log_request(
                req["request_id"], req["prompt"], req["model"],
                req["prompt_tokens"], req["completion_tokens"], latency,
                prompt_version=req["prompt_version"],
                model_version=req["model_version"])
    summary = aggregate(logger.records)
    spans = tracer.spans()
    out = {
        "label": "simulated requests only, no real LLM call",
        "records": logger.records,
        "summary": summary,
        "cost_check": {"matched": cost_matched, "total": len(requests)},
        "registry_changelog": registry.changelog(),
        "trace_summary": {
            "span_count": len(spans),
            "root_count": len(tracer.roots()),
            "spans": spans,
        },
    }
    path = os.path.join(HERE, "results_learn.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    print("Simulated requests:", summary["count"])
    print("Total tokens:", summary["total_tokens"],
          "(prompt", summary["prompt_tokens"],
          "+ completion", summary["completion_tokens"], ")")
    print("Total cost USD:", summary["total_cost_usd"])
    print("Cost labels matched:", cost_matched, "of", len(requests))
    print("Mean latency ms:", summary["mean_latency_ms"],
          "p50:", summary["p50_latency_ms"],
          "p95:", summary["p95_latency_ms"])
    print("Spans:", len(spans), "roots:", len(tracer.roots()))
    print("Wrote", path)
    return 0 if cost_matched == len(requests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
