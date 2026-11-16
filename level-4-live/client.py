"""Level 4 Live: the workload driver for the observation window.

Sends genuine document questions to the live service (server.py), one
at a time, in a seeded shuffled rotation over the bundled corpus, with
a jittered gap between requests. Every attempt is logged client-side
as one JSON line, including failures, so the client log and the
service store can be cross-checked.

This driver is a program, and the results say so: the traffic is a
shipped client asking real questions of a real model on a schedule.
It is not organic user traffic and is never described as such.

Usage:
    python3 client.py --url http://127.0.0.1:18081 --count 340 \
        --min-gap 15 --max-gap 27 --seed 20251115 --log client_log.jsonl
"""
import argparse
import json
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from live import iter_questions, load_corpus


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def build_rotation(questions, seed):
    """Deterministic shuffled rotation of question ids."""
    ids = [q["id"] for _d, q in questions]
    random.Random(seed).shuffle(ids)
    return ids


def ask_once(url, question_id, timeout_s):
    body = json.dumps({"question_id": question_id}).encode("utf-8")
    req = urllib.request.Request(url + "/ask", data=body,
                                 headers={"Content-Type": "application/json"})
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            http_status = resp.status
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        http_status = exc.code
    client_latency_ms = int((time.monotonic() - started) * 1000)
    return http_status, payload, client_latency_ms


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:18081")
    parser.add_argument("--count", type=int, default=340)
    parser.add_argument("--min-gap", type=float, default=15.0)
    parser.add_argument("--max-gap", type=float, default=27.0)
    parser.add_argument("--seed", type=int, default=20251115)
    parser.add_argument("--timeout", type=float, default=150.0)
    parser.add_argument("--log", default="client_log.jsonl")
    args = parser.parse_args()

    questions = iter_questions(load_corpus())
    rotation = build_rotation(questions, args.seed)
    rng = random.Random(args.seed + 1)
    print("client start %s count=%d rotation=%d questions" % (
        utc_now_iso(), args.count, len(rotation)), flush=True)
    with open(args.log, "a", encoding="utf-8") as log:
        for n in range(1, args.count + 1):
            question_id = rotation[(n - 1) % len(rotation)]
            entry = {"n": n, "timestamp_utc": utc_now_iso(),
                     "question_id": question_id}
            try:
                http_status, payload, client_ms = ask_once(
                    args.url, question_id, args.timeout)
                entry.update({
                    "http_status": http_status,
                    "client_latency_ms": client_ms,
                    "status": payload.get("status"),
                    "service_latency_ms": payload.get("latency_ms"),
                    "answer_check_pass": payload.get("answer_check_pass"),
                    "error": payload.get("error"),
                })
            except Exception as exc:  # a failed attempt is logged, not hidden
                entry.update({"http_status": None, "client_latency_ms": None,
                              "status": "client-error",
                              "service_latency_ms": None,
                              "answer_check_pass": None,
                              "error": type(exc).__name__ + ": " + str(exc)[:200]})
            log.write(json.dumps(entry, sort_keys=True) + "\n")
            log.flush()
            print("attempt %d %s -> %s" % (n, question_id, entry["status"]),
                  flush=True)
            if n < args.count:
                time.sleep(rng.uniform(args.min_gap, args.max_gap))
    print("client done %s" % utc_now_iso(), flush=True)


if __name__ == "__main__":
    main()
