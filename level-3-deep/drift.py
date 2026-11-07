"""Level 3 Deep: quality drift detection and alerts, stdlib only.

Compares a baseline window against a current window of request logs.
Records are dicts with fields: latency_ms, total_tokens, cost_usd,
quality_pass (bool). The quality field is a simulated logged field in
this project; this module treats it as data and makes no claim that
it is real model quality.

Named statistics used:
1. Population Stability Index (PSI) on binned distributions for the
   numeric metrics (latency, tokens, cost).
2. Mean shift in pooled standard deviation units for numeric metrics.
3. Two-proportion z check for the simulated quality pass rate.
4. Two-sample Kolmogorov-Smirnov statistic as a distribution-free
   baseline next to PSI. It is reported, not used for severity.

Thresholds are documented constants below, not learned values. The
reasons are stated next to each constant.
"""

import math
from statistics import NormalDist

# PSI thresholds: common practice in drift literature treats PSI
# below 0.1 as no significant change, 0.1 to 0.25 as moderate, and
# above 0.25 as significant. Kept as stated constants here.
PSI_WARNING = 0.10
PSI_ALERT = 0.25

# Mean shift thresholds in pooled SD units: 0.5 SD is a medium effect
# (Cohen convention), 1.0 SD is a large effect.
MEAN_SHIFT_WARNING = 0.5
MEAN_SHIFT_ALERT = 1.0

# Pass rate thresholds: absolute drop and z magnitude. A drop of
# 0.05 is a warning signal when also statistically notable; a drop
# of 0.10 with |z| above 1.96 (5 percent two-sided) is an alert.
PASS_RATE_WARNING_DROP = 0.05
PASS_RATE_ALERT_DROP = 0.10
Z_ALERT = 1.96

EPS = 1e-4

# Family-wise alpha for the informational multiple-comparison fields.
# Four metrics are checked per window, so a per-test 1.96 cut-off
# overstates confidence. KS uses alpha / 3 (three numeric metrics);
# the pass rate reports the z cut-off at alpha / 4, two-sided.
KS_FAMILY_ALPHA = 0.05
N_METRICS = 4
Z_BONFERRONI = round(NormalDist().inv_cdf(1 - KS_FAMILY_ALPHA / (2 * N_METRICS)), 6)

SEVERITY_ORDER = ["none", "low", "medium", "high"]


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _variance(values, mean):
    if len(values) < 2:
        return 0.0
    return sum((v - mean) ** 2 for v in values) / (len(values) - 1)


def population_stability_index(baseline, current, bins=10):
    """PSI between baseline and current numeric samples.

    Bins are baseline quantile edges. Each bin proportion is smoothed
    with EPS to avoid log of zero. Identical distributions give PSI
    near 0. Returns a float rounded to 6 places.
    """
    if not baseline or not current:
        raise ValueError("PSI needs non-empty samples")
    ordered = sorted(baseline)
    n = len(ordered)
    edges = []
    for i in range(1, bins):
        idx = min(n - 1, max(0, int(round(i * n / bins)) - 1))
        edges.append(ordered[idx])
    # Deduplicate edges preserving order.
    uniq = []
    for e in edges:
        if not uniq or e != uniq[-1]:
            uniq.append(e)
    edges = uniq

    def proportions(values):
        counts = [0] * (len(edges) + 1)
        for v in values:
            placed = len(edges)
            for i, edge in enumerate(edges):
                if v <= edge:
                    placed = i
                    break
            counts[placed] += 1
        total = len(values)
        return [(c / total if total else 0.0) for c in counts]

    base_p = proportions(baseline)
    cur_p = proportions(current)
    psi = 0.0
    for b, c in zip(base_p, cur_p):
        b_s = max(b, EPS)
        c_s = max(c, EPS)
        psi += (c_s - b_s) * math.log(c_s / b_s)
    return round(psi, 6)


def mean_shift_pooled_sd(baseline, current):
    """(mean_current - mean_baseline) / pooled SD, rounded to 6."""
    if not baseline or not current:
        raise ValueError("mean shift needs non-empty samples")
    mb = _mean(baseline)
    mc = _mean(current)
    vb = _variance(baseline, mb)
    vc = _variance(current, mc)
    nb = len(baseline)
    nc = len(current)
    if nb + nc - 2 <= 0:
        return 0.0
    pooled_var = ((nb - 1) * vb + (nc - 1) * vc) / (nb + nc - 2)
    pooled_sd = math.sqrt(pooled_var) if pooled_var > 0 else 0.0
    if pooled_sd == 0:
        return 0.0 if mc == mb else round(float("inf"), 6)
    return round((mc - mb) / pooled_sd, 6)


def two_proportion_z(baseline_passes, baseline_n, current_passes, current_n):
    """Two-proportion z statistic for pass rates. Returns (z, p_base, p_cur)."""
    if baseline_n == 0 or current_n == 0:
        raise ValueError("proportions need non-zero counts")
    p1 = baseline_passes / baseline_n
    p2 = current_passes / current_n
    p_pool = (baseline_passes + current_passes) / (baseline_n + current_n)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / baseline_n + 1 / current_n)) if 0 < p_pool < 1 else 0.0
    # SE is 0 only when the pooled rate is 0 or 1, which forces p1 == p2,
    # so z is 0 by definition there (no division).
    z = 0.0 if se == 0 else (p2 - p1) / se
    return round(z, 6), round(p1, 6), round(p2, 6)


def ks_statistic(baseline, current):
    """Two-sample Kolmogorov-Smirnov D (max ECDF gap), rounded to 6."""
    if not baseline or not current:
        raise ValueError("KS needs non-empty samples")
    a = sorted(baseline)
    b = sorted(current)
    i = j = 0
    d = 0.0
    while i < len(a) and j < len(b):
        v = min(a[i], b[j])
        while i < len(a) and a[i] == v:
            i += 1
        while j < len(b) and b[j] == v:
            j += 1
        d = max(d, abs(i / len(a) - j / len(b)))
    return round(d, 6)


def ks_critical(n, m, alpha):
    """Asymptotic two-sample KS critical value at level alpha."""
    return round(math.sqrt(-math.log(alpha / 2) / 2) * math.sqrt((n + m) / (n * m)), 6)


def _severity_numeric(psi, shift):
    psi_sev = "high" if psi >= PSI_ALERT else ("medium" if psi >= PSI_WARNING else "none")
    abs_shift = abs(shift) if shift != float("inf") else 99.0
    shift_sev = "high" if abs_shift >= MEAN_SHIFT_ALERT else ("medium" if abs_shift >= MEAN_SHIFT_WARNING else "none")
    # Overall for this metric is the higher of the two signals.
    return psi_sev if SEVERITY_ORDER.index(psi_sev) >= SEVERITY_ORDER.index(shift_sev) else shift_sev


def assess_numeric_metric(name, baseline_values, current_values):
    psi = population_stability_index(baseline_values, current_values)
    shift = mean_shift_pooled_sd(baseline_values, current_values)
    severity = _severity_numeric(psi, shift)
    ks = ks_statistic(baseline_values, current_values)
    ks_crit = ks_critical(len(baseline_values), len(current_values), KS_FAMILY_ALPHA / 3)
    return {
        "metric": name,
        "baseline_mean": round(_mean(baseline_values), 6),
        "current_mean": round(_mean(current_values), 6),
        "psi": psi,
        "mean_shift_pooled_sd": shift,
        "psi_warning_threshold": PSI_WARNING,
        "psi_alert_threshold": PSI_ALERT,
        "mean_shift_warning_threshold": MEAN_SHIFT_WARNING,
        "mean_shift_alert_threshold": MEAN_SHIFT_ALERT,
        "ks_statistic": ks,
        "ks_critical_bonferroni": ks_crit,
        "ks_reject": ks > ks_crit,
        "severity": severity,
        "alert": severity in ("medium", "high"),
    }


def assess_pass_rate(baseline_records, current_records):
    b_pass = sum(1 for r in baseline_records if r.get("quality_pass"))
    c_pass = sum(1 for r in current_records if r.get("quality_pass"))
    z, p_base, p_cur = two_proportion_z(b_pass, len(baseline_records), c_pass, len(current_records))
    drop = round(p_base - p_cur, 6)
    if drop >= PASS_RATE_ALERT_DROP and abs(z) >= Z_ALERT:
        severity = "high"
    elif drop >= PASS_RATE_WARNING_DROP:
        severity = "medium"
    elif drop > 0.02:
        severity = "low"
    else:
        severity = "none"
    return {
        "metric": "quality_pass_rate_simulated",
        "baseline_pass_rate": p_base,
        "current_pass_rate": p_cur,
        "drop": drop,
        "z": z,
        "z_alert_threshold": Z_ALERT,
        "z_bonferroni_threshold": Z_BONFERRONI,
        "survives_bonferroni": drop > 0 and abs(z) >= Z_BONFERRONI,
        "direction": "drop only",
        "alert_drop_threshold": PASS_RATE_ALERT_DROP,
        "warning_drop_threshold": PASS_RATE_WARNING_DROP,
        "severity": severity,
        "alert": severity in ("medium", "high"),
        "note": "quality_pass is a simulated logged field, not real model quality",
    }


def detect_drift(baseline_records, current_records):
    """Full drift report comparing two windows of records."""
    if not baseline_records or not current_records:
        raise ValueError("both windows must be non-empty")
    per_metric = {}
    for field, label in (("latency_ms", "latency_ms"), ("total_tokens", "total_tokens"), ("cost_usd", "cost_usd")):
        per_metric[label] = assess_numeric_metric(
            label,
            [float(r[field]) for r in baseline_records],
            [float(r[field]) for r in current_records],
        )
    per_metric["quality_pass_rate_simulated"] = assess_pass_rate(baseline_records, current_records)
    alerts = []
    for key, result in per_metric.items():
        if result["alert"]:
            alerts.append({"metric": key, "severity": result["severity"]})
    overall = "none"
    for result in per_metric.values():
        if SEVERITY_ORDER.index(result["severity"]) > SEVERITY_ORDER.index(overall):
            overall = result["severity"]
    return {
        "baseline_count": len(baseline_records),
        "current_count": len(current_records),
        "per_metric": per_metric,
        "alerts": alerts,
        "alert_count": len(alerts),
        "overall_severity": overall,
        "has_alert": len(alerts) > 0,
    }
