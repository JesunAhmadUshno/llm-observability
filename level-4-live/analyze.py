"""Level 4 Live: analyze the observation window into results_live.json.

Reads the JSONL store the live service wrote (through the Level 2
LogStore, the same reader the simulated levels use) and computes:
request counts and error rate, latency percentiles (the repo's own
nearest-rank percentile), token totals from the model server's usage
counts, payload sizes, the answer-check pass rate, and a drift
comparison between the first and second halves of the window using
the Level 3 statistics (PSI and pooled-SD mean shift per metric, and
the two-proportion z for the answer-check rate).

Every number in the output comes from the store file named on the
command line. Nothing is estimated and nothing is filled in.

Usage:
    python3 analyze.py --store store_live.jsonl --out results_live.json \
        --host-label BlackBoxV3 --model-sha256 <sha256 of the GGUF file> \
        --runtime "llama.cpp b12418, llama-server, CPU, 6 threads" \
        --anomaly-note "text written after inspecting anomaly_candidates"
"""
import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _d in (os.path.join(ROOT, "level-1-learn"), os.path.join(ROOT, "level-2-build"),
           os.path.join(ROOT, "level-3-deep")):
    if _d not in sys.path:
        sys.path.insert(0, _d)

from drift import assess_numeric_metric, two_proportion_z  # noqa: E402
from live import MODEL_NAME, MODEL_VERSION  # noqa: E402
from observability import aggregate, percentile  # noqa: E402
from service import LogStore  # noqa: E402


def _latency_block(records):
    lat = [r["latency_ms"] for r in records]
    if not lat:
        return {"count": 0}
    summary = aggregate(records)
    return {
        "count": len(lat),
        "mean_ms": summary["mean_latency_ms"],
        "p50_ms": summary["p50_latency_ms"],
        "p95_ms": summary["p95_latency_ms"],
        "p99_ms": percentile(lat, 99),
        "min_ms": min(lat),
        "max_ms": max(lat),
    }


def _pass_block(records):
    n = len(records)
    passes = sum(1 for r in records if r.get("answer_check_pass"))
    return {"n": n, "passes": passes,
            "pass_rate": round(passes / n, 6) if n else 0.0}


def _by_question(records):
    out = {}
    for r in records:
        block = out.setdefault(r.get("question_id"), {"n": 0, "passes": 0})
        block["n"] += 1
        block["passes"] += 1 if r.get("answer_check_pass") else 0
    for block in out.values():
        block["pass_rate"] = round(block["passes"] / block["n"], 6) if block["n"] else 0.0
    return out


def analyze(records, meta, anomaly_note=None):
    ok = [r for r in records if r.get("status") == "ok"]
    errors = [r for r in records if r.get("status") != "ok"]
    total = len(records)
    half = total // 2
    first, second = records[:half], records[half:]
    first_ok = [r for r in first if r.get("status") == "ok"]
    second_ok = [r for r in second if r.get("status") == "ok"]

    drift = {}
    if first_ok and second_ok:
        for field in ("latency_ms", "total_tokens"):
            drift[field] = assess_numeric_metric(
                field,
                [float(r[field]) for r in first_ok],
                [float(r[field]) for r in second_ok],
            )
    pass_first = _pass_block(first_ok)
    pass_second = _pass_block(second_ok)
    z_block = None
    if pass_first["n"] and pass_second["n"]:
        z, p1, p2 = two_proportion_z(pass_first["passes"], pass_first["n"],
                                     pass_second["passes"], pass_second["n"])
        z_block = {"z": z, "first_half_pass_rate": p1,
                   "second_half_pass_rate": p2,
                   "note": "two-proportion z on the mechanical answer check"}

    lat = _latency_block(ok)
    p95 = lat.get("p95_ms", 0)
    slow_threshold = 3 * p95 if p95 else None
    candidates = []
    for r in errors:
        candidates.append({"kind": "error", "request_id": r["request_id"],
                           "question_id": r.get("question_id"),
                           "error": r.get("error")})
    if slow_threshold:
        for r in ok:
            if r["latency_ms"] > slow_threshold:
                candidates.append({"kind": "slow_outlier",
                                   "request_id": r["request_id"],
                                   "question_id": r.get("question_id"),
                                   "latency_ms": r["latency_ms"],
                                   "threshold_ms": slow_threshold})
    for key, block in drift.items():
        if block.get("alert"):
            candidates.append({"kind": "drift_alert", "metric": key,
                               "severity": block["severity"],
                               "psi": block["psi"],
                               "mean_shift_pooled_sd": block["mean_shift_pooled_sd"]})
    by_question = _by_question(ok)
    for question_id, block in sorted(by_question.items()):
        if block["n"] >= 10 and block["passes"] == 0:
            candidates.append({"kind": "answer_check_all_fail",
                               "question_id": question_id,
                               "attempts": block["n"], "passes": 0})
    slowest = sorted(ok, key=lambda r: r["latency_ms"], reverse=True)[:5]

    duration_s = None
    if records:
        start = datetime.fromisoformat(records[0]["timestamp_utc"])
        end = datetime.fromisoformat(records[-1]["timestamp_utc"])
        duration_s = round((end - start).total_seconds(), 3)

    return {
        "kind": "live-observation",
        "generated_by": "level-4-live/analyze.py",
        "traffic": {
            "what": "A shipped client program (level-4-live/client.py) asked "
                    "genuine questions about the bundled project documents "
                    "(level-4-live/corpus.json) to an instrumented service "
                    "(level-4-live/server.py), which called a real local model "
                    "for every request.",
            "honest_label": "Program-driven workload on a personal fleet "
                            "machine. Not organic user traffic, not "
                            "production traffic, not production scale.",
            "generator": "level-4-live/client.py, seeded rotation, jittered gaps",
        },
        "deployment": meta,
        "model": {"name": MODEL_NAME, "version": MODEL_VERSION},
        "window": {
            "start_utc": records[0]["timestamp_utc"] if records else None,
            "end_utc": records[-1]["timestamp_utc"] if records else None,
            "duration_s": duration_s,
            "records": total,
        },
        "requests": {
            "total": total,
            "ok": len(ok),
            "errors": len(errors),
            "error_rate": round(len(errors) / total, 6) if total else 0.0,
        },
        "latency_ms": lat,
        "tokens": {
            "prompt_total": sum(r["prompt_tokens"] for r in ok),
            "completion_total": sum(r["completion_tokens"] for r in ok),
            "total": sum(r["total_tokens"] for r in ok),
            "prompt_mean": round(sum(r["prompt_tokens"] for r in ok) / len(ok), 3) if ok else 0,
            "completion_mean": round(sum(r["completion_tokens"] for r in ok) / len(ok), 3) if ok else 0,
            "source": "model server usage field (token_source per record)",
            "token_sources": sorted({r.get("token_source") for r in ok}),
        },
        "payload_chars": {
            "prompt_mean": round(sum(r["prompt_chars"] for r in ok) / len(ok), 3) if ok else 0,
            "prompt_max": max((r["prompt_chars"] for r in ok), default=0),
            "completion_mean": round(sum(r["completion_chars"] for r in ok) / len(ok), 3) if ok else 0,
            "completion_max": max((r["completion_chars"] for r in ok), default=0),
        },
        "answer_check": {
            "method": "The completion contains the expected answer string "
                      "from the document (case-insensitive substring). A "
                      "mechanical check on a real completion, not a human "
                      "quality judgement.",
            "overall": _pass_block(ok),
            "by_question": by_question,
            "first_half": pass_first,
            "second_half": pass_second,
            "two_proportion_z": z_block,
        },
        "drift_first_vs_second_half": drift,
        "slowest_requests": [
            {"request_id": r["request_id"], "question_id": r.get("question_id"),
             "latency_ms": r["latency_ms"]} for r in slowest
        ],
        "errors": [
            {"request_id": r["request_id"], "question_id": r.get("question_id"),
             "latency_ms": r["latency_ms"], "error": r.get("error")} for r in errors
        ],
        "anomaly_candidates": candidates,
        "anomaly": {
            "found": bool(candidates),
            "note": anomaly_note or "Not yet written: run once, inspect "
                                    "anomaly_candidates, then re-run with "
                                    "--anomaly-note.",
        },
        "store_file": "level-4-live/store_live.jsonl",
        "claims_ceiling": "Real-traffic observation of one small local model "
                          "on one personal fleet machine, at the scale "
                          "recorded in the window above. Nothing here is "
                          "evidence about production LLM traffic.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--host-label", required=True)
    parser.add_argument("--model-sha256", required=True)
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--anomaly-note", default=None)
    args = parser.parse_args()

    records = LogStore(args.store).load_records()
    if not records:
        raise SystemExit("no records in store: " + args.store)
    meta = {
        "host": args.host_label,
        "runtime": args.runtime,
        "model_file_sha256": args.model_sha256,
        "service": "level-4-live/server.py on 127.0.0.1, model server on "
                   "127.0.0.1, both on the same host",
    }
    results = analyze(records, meta, anomaly_note=args.anomaly_note)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)
        f.write("\n")
    print("wrote %s from %d records" % (args.out, len(records)))


if __name__ == "__main__":
    main()
