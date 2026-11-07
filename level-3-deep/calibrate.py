"""Level 3 Deep calibration: how often does the detector cry wolf, and how much drift can it see?

run_deep.py uses one seed per window, so it shows the detector works once.
This study repeats the same seeded generator many times, stdlib only, CPU,
a few seconds:

1. False-alert rate: baseline vs no-drift control at window sizes
   100 to 2000, REPS independent seed pairs each. Reported for the
   overall has_alert flag and per metric, with Wilson 95% intervals.
2. Detection power at POWER_N records: latency mean shifts and simulated
   pass-rate drops, REPS seed pairs per setting. For latency the KS
   baseline (Bonferroni alpha 0.05 / 3) is reported next to the
   PSI / mean-shift rule.
3. Sequential setting: a one-sided CUSUM on latency (k = 0.5 SD,
   h = 5 SD, baseline mean and SD estimated from a baseline window)
   over a stream whose mean steps up after STREAM_PRE records. Reports
   false alarms before the change and detection delay after it.

Everything is simulated with the run_deep generator. Quality is a
simulated logged field. Writes level-3-deep/results_calibration.json,
identical across runs (no timing field).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from drift import detect_drift  # noqa: E402
from run_deep import generate_window  # noqa: E402

BASE = {"latency_mean": 500.0, "tokens_mean": 1500.0, "cost_per_token": 0.0006, "pass_rate": 0.92}
SIZES = (100, 200, 500, 1000, 2000)
REPS = 50
POWER_N = 1000
LATENCY_SHIFTS_MS = (5.0, 10.0, 20.0, 40.0, 80.0)
PASS_RATES = (0.90, 0.88, 0.86, 0.84, 0.82, 0.80)
# Seed pair for repetition r: baseline 10000 + 2r, current 10001 + 2r.
SEED_BASE = 10000
CUSUM_K = 0.5
CUSUM_H = 5.0
STREAM_PRE = 500
STREAM_POST = 500
STREAM_SHIFT_MS = 40.0
METRICS = ("latency_ms", "total_tokens", "cost_usd", "quality_pass_rate_simulated")


def wilson(k, n, z=1.959964):
    """Wilson score 95% interval for k successes in n trials, rounded to 4."""
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def _window(seed, n, latency_mean=None, pass_rate=None):
    return generate_window(seed, latency_mean or BASE["latency_mean"], BASE["tokens_mean"],
                           BASE["cost_per_token"], pass_rate or BASE["pass_rate"], n=n)


def _rate(k, n):
    return {"count": k, "runs": n, "rate": round(k / n, 4), "ci95": wilson(k, n)}


def cusum_first_alarm(values, mu, sd, k=CUSUM_K, h=CUSUM_H):
    """Index of the first upper-CUSUM alarm, or None. Restarts are not modelled."""
    s = 0.0
    for i, v in enumerate(values):
        s = max(0.0, s + (v - mu) / sd - k)
        if s > h:
            return i
    return None


def false_alert(sizes, reps):
    rows = []
    for n in sizes:
        any_alert = 0
        per = {m: 0 for m in METRICS}
        for r in range(reps):
            report = detect_drift(_window(SEED_BASE + 2 * r, n), _window(SEED_BASE + 2 * r + 1, n))
            any_alert += report["has_alert"]
            for m in METRICS:
                per[m] += report["per_metric"][m]["alert"]
        rows.append({"n": n, "runs": reps, "any_alert": any_alert, "any_alert_rate": round(any_alert / reps, 4),
                     "ci95": wilson(any_alert, reps), "per_metric_alerts": per})
    return rows


def power(reps, n):
    lat = []
    for shift in LATENCY_SHIFTS_MS:
        alert = ks = 0
        for r in range(reps):
            report = detect_drift(_window(SEED_BASE + 2 * r, n),
                                  _window(SEED_BASE + 2 * r + 1, n, latency_mean=BASE["latency_mean"] + shift))
            alert += report["per_metric"]["latency_ms"]["alert"]
            ks += report["per_metric"]["latency_ms"]["ks_reject"]
        lat.append({"shift_ms": shift, "shift_sd": round(shift / 80.0, 4),
                    "rule": _rate(alert, reps), "ks": _rate(ks, reps)})
    qual = []
    for rate in PASS_RATES:
        alert = bonf = 0
        for r in range(reps):
            report = detect_drift(_window(SEED_BASE + 2 * r, n), _window(SEED_BASE + 2 * r + 1, n, pass_rate=rate))
            pr = report["per_metric"]["quality_pass_rate_simulated"]
            alert += pr["alert"]
            bonf += pr["survives_bonferroni"]
        qual.append({"pass_rate": rate, "true_drop": round(BASE["pass_rate"] - rate, 4),
                     "rule": _rate(alert, reps), "bonferroni": _rate(bonf, reps)})
    return {"n": n, "latency_shift": lat, "pass_rate_drop": qual}


def cusum_study(reps):
    false_alarms = 0
    delays = []
    missed = 0
    for r in range(reps):
        base = [x["latency_ms"] for x in _window(SEED_BASE + 2 * r, POWER_N)]
        mu = sum(base) / len(base)
        sd = math.sqrt(sum((v - mu) ** 2 for v in base) / (len(base) - 1))
        pre = [x["latency_ms"] for x in _window(50000 + 2 * r, STREAM_PRE)]
        post = [x["latency_ms"] for x in _window(50001 + 2 * r, STREAM_POST,
                                                  latency_mean=BASE["latency_mean"] + STREAM_SHIFT_MS)]
        alarm = cusum_first_alarm(pre + post, mu, sd)
        if alarm is None:
            missed += 1
        elif alarm < STREAM_PRE:
            false_alarms += 1
        else:
            delays.append(alarm - STREAM_PRE + 1)
    delays.sort()
    return {
        "k_sd": CUSUM_K, "h_sd": CUSUM_H, "pre_change_records": STREAM_PRE, "post_change_records": STREAM_POST,
        "shift_ms": STREAM_SHIFT_MS, "shift_sd": round(STREAM_SHIFT_MS / 80.0, 4), "runs": reps,
        "false_alarm_before_change": _rate(false_alarms, reps),
        "missed": missed,
        "detected": len(delays),
        "delay_records_median": delays[len(delays) // 2] if delays else None,
        "delay_records_min": delays[0] if delays else None,
        "delay_records_max": delays[-1] if delays else None,
    }


def run_calibration(sizes=SIZES, reps=REPS, power_n=POWER_N):
    return {
        "experiment": "detector_calibration_over_seeds",
        "label": "simulated: run_deep generator, quality_pass is a simulated logged field",
        "baseline_params": BASE,
        "reps": reps,
        "seed_rule": "repetition r uses baseline seed %d + 2r and current seed %d + 2r + 1" % (SEED_BASE, SEED_BASE),
        "bins": 10,
        "false_alert": false_alert(sizes, reps),
        "power": power(reps, power_n),
        "cusum_latency": cusum_study(reps),
    }


def main():
    out = run_calibration()
    path = os.path.join(HERE, "results_calibration.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    for row in out["false_alert"]:
        print("false alert n=%d: %d/%d %s" % (row["n"], row["any_alert"], row["runs"], row["ci95"]))
    return out


if __name__ == "__main__":
    main()
