"""Level 3 Deep runner: seeded simulated drift experiment, stdlib only.

Generates four windows, each 1000 records, from seeded generators:
- baseline: reference distribution
- control_no_drift: same distribution as baseline, different seed
- latency_cost_drift: latency and tokens and cost shifted up
- quality_drift: simulated quality pass rate drops, other metrics
  near baseline

Quality is a simulated logged field (quality_pass) in every window.
It is labelled simulated everywhere and is never real model quality.

Writes level-3-deep/results_deep.json deterministically across runs
except no timing field is included, so the file is fully identical
across two runs on the same code.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from drift import detect_drift  # noqa: E402

N = 1000


def _record(rng, latency_mean, latency_sd, tokens_mean, tokens_sd, cost_per_token, pass_rate):
    latency = max(10.0, rng.gauss(latency_mean, latency_sd))
    tokens = max(10, int(round(rng.gauss(tokens_mean, tokens_sd))))
    cost = round(tokens * cost_per_token * rng.uniform(0.9, 1.1), 6)
    return {
        "latency_ms": round(latency, 3),
        "total_tokens": tokens,
        "cost_usd": cost,
        "quality_pass": rng.random() < pass_rate,
        "quality_label": "simulated",
    }


def generate_window(seed, latency_mean, tokens_mean, cost_per_token, pass_rate,
                    latency_sd=80.0, tokens_sd=300.0, n=N):
    rng = random.Random(seed)
    return [_record(rng, latency_mean, latency_sd, tokens_mean, tokens_sd, cost_per_token, pass_rate)
            for _ in range(n)]


def build_experiment():
    baseline = generate_window(1201, 500.0, 1500.0, 0.0006, 0.92)
    control = generate_window(2202, 500.0, 1500.0, 0.0006, 0.92)
    latency_cost = generate_window(3203, 850.0, 2200.0, 0.0009, 0.91)
    quality = generate_window(4204, 510.0, 1520.0, 0.0006, 0.62)
    windows = {
        "control_no_drift": control,
        "latency_cost_drift": latency_cost,
        "quality_drift": quality,
    }
    results = {}
    for name, window in windows.items():
        results[name] = detect_drift(baseline, window)
    summary = {
        "experiment": "seeded_simulated_drift_experiment",
        "quality_label": "simulated: quality_pass is a simulated logged field, not real model quality",
        "n_per_window": N,
        "seeds": {"baseline": 1201, "control_no_drift": 2202, "latency_cost_drift": 3203, "quality_drift": 4204},
        "baseline_params": {"latency_mean_ms": 500.0, "tokens_mean": 1500.0,
                            "cost_per_token": 0.0006, "pass_rate": 0.92},
        "windows": results,
        "success_criteria": {
            "control_no_alert_or_low_only": results["control_no_drift"]["overall_severity"] in ("none", "low"),
            "latency_cost_alert_fired": results["latency_cost_drift"]["has_alert"],
            "quality_alert_fired": results["quality_drift"]["has_alert"],
        },
    }
    summary["success_criteria"]["all_passed"] = all(summary["success_criteria"].values())
    return summary


def main():
    summary = build_experiment()
    out = os.path.join(HERE, "results_deep.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(summary["success_criteria"], sort_keys=True))
    for name, res in summary["windows"].items():
        print(name, "overall", res["overall_severity"], "alerts", res["alert_count"])
    return summary


if __name__ == "__main__":
    main()
