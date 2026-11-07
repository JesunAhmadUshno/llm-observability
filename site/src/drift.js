// JS port of level-3-deep/drift.py and the generator in level-3-deep/run_deep.py.
// PyRandom reproduces CPython's random.Random (MT19937, init_by_array seeding,
// 53-bit random(), cached gauss pair) so the browser re-runs the recorded
// experiment record for record. drift.check.mjs proves it at build time.

export class PyRandom {
  constructor(seed) {
    this.mt = new Uint32Array(624);
    this.mti = 625;
    this.gaussNext = null;
    this.initByArray([Math.abs(seed) >>> 0]); // seeds used here fit in one 32-bit word
  }
  initGenrand(s) {
    const mt = this.mt;
    mt[0] = s >>> 0;
    for (let i = 1; i < 624; i++) {
      const p = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = (Math.imul(1812433253, p) + i) >>> 0;
    }
    this.mti = 624;
  }
  initByArray(key) {
    const mt = this.mt;
    this.initGenrand(19650218);
    let i = 1, j = 0;
    for (let k = Math.max(624, key.length); k; k--) {
      const p = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = ((mt[i] ^ Math.imul(p, 1664525)) + key[j] + j) >>> 0;
      i++; j++;
      if (i >= 624) { mt[0] = mt[623]; i = 1; }
      if (j >= key.length) j = 0;
    }
    for (let k = 623; k; k--) {
      const p = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = ((mt[i] ^ Math.imul(p, 1566083941)) - i) >>> 0;
      i++;
      if (i >= 624) { mt[0] = mt[623]; i = 1; }
    }
    mt[0] = 0x80000000;
  }
  genrand() {
    const mt = this.mt;
    if (this.mti >= 624) {
      for (let kk = 0; kk < 624; kk++) {
        const y = (mt[kk] & 0x80000000) | (mt[(kk + 1) % 624] & 0x7fffffff);
        mt[kk] = mt[(kk + 397) % 624] ^ (y >>> 1) ^ (y & 1 ? 0x9908b0df : 0);
      }
      this.mti = 0;
    }
    let y = mt[this.mti++];
    y ^= y >>> 11;
    y ^= (y << 7) & 0x9d2c5680;
    y ^= (y << 15) & 0xefc60000;
    y ^= y >>> 18;
    return y >>> 0;
  }
  random() {
    const a = this.genrand() >>> 5, b = this.genrand() >>> 6;
    return (a * 67108864 + b) / 9007199254740992;
  }
  uniform(a, b) { return a + (b - a) * this.random(); }
  gauss(mu, sigma) {
    let z = this.gaussNext;
    this.gaussNext = null;
    if (z === null) {
      const x2pi = this.random() * 2 * Math.PI;
      const g2rad = Math.sqrt(-2 * Math.log(1 - this.random()));
      z = Math.cos(x2pi) * g2rad;
      this.gaussNext = Math.sin(x2pi) * g2rad;
    }
    return mu + z * sigma;
  }
}

// Python round(x, d) on a double: toFixed rounds the exact binary value, like CPython.
// Exact decimal ties (vanishingly rare for these values) would go up here, half-even in Python.
export const pyRound = (x, d) => (Number.isFinite(x) ? Number(x.toFixed(d)) : x);
// Python round(x) to an integer: banker's rounding on exact .5.
export const roundHalfEven = (x) => {
  const r = Math.round(x);
  return Math.abs(x % 1) === 0.5 ? 2 * Math.round(x / 2) : r;
};

// CPython 3.12+ sum() of floats uses Neumaier compensated summation.
export function pySum(values) {
  let s = 0, c = 0;
  for (const x of values) {
    const t = s + x;
    c += Math.abs(s) >= Math.abs(x) ? (s - t) + x : (x - t) + s;
    s = t;
  }
  return c && Number.isFinite(c) ? s + c : s;
}

// Thresholds are parsed from drift.py's source so the page can never drift from it.
export function parseThresholds(src) {
  const get = (name) => {
    const m = src.match(new RegExp(`^${name}\\s*=\\s*([0-9.eE+-]+)`, 'm'));
    if (!m) throw new Error(`threshold ${name} not found in drift.py`);
    return Number(m[1]);
  };
  return Object.fromEntries(['PSI_WARNING', 'PSI_ALERT', 'MEAN_SHIFT_WARNING', 'MEAN_SHIFT_ALERT',
    'PASS_RATE_WARNING_DROP', 'PASS_RATE_ALERT_DROP', 'Z_ALERT', 'EPS', 'KS_FAMILY_ALPHA'].map((k) => [k, get(k)]));
}

const SEV = ['none', 'low', 'medium', 'high'];
const mean = (v) => (v.length ? pySum(v) / v.length : 0);
const variance = (v, m) => (v.length < 2 ? 0 : pySum(v.map((x) => (x - m) * (x - m))) / (v.length - 1));

export function psi(baseline, current, T, bins = 10) {
  const ordered = [...baseline].sort((a, b) => a - b);
  const n = ordered.length;
  const edges = [];
  for (let i = 1; i < bins; i++) {
    const idx = Math.min(n - 1, Math.max(0, roundHalfEven((i * n) / bins) - 1));
    const e = ordered[idx];
    if (!edges.length || e !== edges[edges.length - 1]) edges.push(e);
  }
  const props = (values) => {
    const counts = new Array(edges.length + 1).fill(0);
    for (const v of values) {
      let placed = edges.length;
      for (let i = 0; i < edges.length; i++) if (v <= edges[i]) { placed = i; break; }
      counts[placed]++;
    }
    return counts.map((c) => c / values.length);
  };
  const bp = props(baseline), cp = props(current);
  let s = 0;
  for (let i = 0; i < bp.length; i++) {
    const b = Math.max(bp[i], T.EPS), c = Math.max(cp[i], T.EPS);
    s += (c - b) * Math.log(c / b);
  }
  return pyRound(s, 6);
}

export function meanShift(baseline, current) {
  const mb = mean(baseline), mc = mean(current);
  const vb = variance(baseline, mb), vc = variance(current, mc);
  const nb = baseline.length, nc = current.length;
  if (nb + nc - 2 <= 0) return 0;
  const pooled = ((nb - 1) * vb + (nc - 1) * vc) / (nb + nc - 2);
  const sd = pooled > 0 ? Math.sqrt(pooled) : 0;
  if (sd === 0) return mc === mb ? 0 : Infinity;
  return pyRound((mc - mb) / sd, 6);
}

// Two-sample Kolmogorov-Smirnov D, the distribution-free baseline next to PSI.
export function ksStatistic(baseline, current) {
  const a = [...baseline].sort((x, y) => x - y), b = [...current].sort((x, y) => x - y);
  let i = 0, j = 0, d = 0;
  while (i < a.length && j < b.length) {
    const v = Math.min(a[i], b[j]);
    while (i < a.length && a[i] === v) i++;
    while (j < b.length && b[j] === v) j++;
    d = Math.max(d, Math.abs(i / a.length - j / b.length));
  }
  return pyRound(d, 6);
}
export const ksCritical = (n, m, alpha) => pyRound(Math.sqrt(-Math.log(alpha / 2) / 2) * Math.sqrt((n + m) / (n * m)), 6);

export function twoProportionZ(bp, bn, cp, cn) {
  const p1 = bp / bn, p2 = cp / cn, pool = (bp + cp) / (bn + cn);
  const se = pool > 0 && pool < 1 ? Math.sqrt(pool * (1 - pool) * (1 / bn + 1 / cn)) : 0;
  const z = se === 0 ? 0 : (p2 - p1) / se;
  return [pyRound(z, 6), pyRound(p1, 6), pyRound(p2, 6)];
}

function numericSeverity(p, shift, T) {
  const ps = p >= T.PSI_ALERT ? 'high' : p >= T.PSI_WARNING ? 'medium' : 'none';
  const a = shift === Infinity ? 99 : Math.abs(shift);
  const ss = a >= T.MEAN_SHIFT_ALERT ? 'high' : a >= T.MEAN_SHIFT_WARNING ? 'medium' : 'none';
  return SEV.indexOf(ps) >= SEV.indexOf(ss) ? ps : ss;
}

export function assessNumeric(name, b, c, T, bins = 10) {
  const p = psi(b, c, T, bins), shift = meanShift(b, c), severity = numericSeverity(p, shift, T);
  const ks = ksStatistic(b, c), crit = ksCritical(b.length, c.length, T.KS_FAMILY_ALPHA / 3);
  return { metric: name, baseline_mean: pyRound(mean(b), 6), current_mean: pyRound(mean(c), 6), psi: p,
    mean_shift_pooled_sd: shift, ks_statistic: ks, ks_critical_bonferroni: crit, ks_reject: ks > crit,
    severity, alert: severity === 'medium' || severity === 'high' };
}

export function assessPassRate(b, c, T) {
  const bp = b.filter((r) => r.quality_pass).length, cp = c.filter((r) => r.quality_pass).length;
  const [z, pb, pc] = twoProportionZ(bp, b.length, cp, c.length);
  const drop = pyRound(pb - pc, 6);
  let severity = 'none';
  if (drop >= T.PASS_RATE_ALERT_DROP && Math.abs(z) >= T.Z_ALERT) severity = 'high';
  else if (drop >= T.PASS_RATE_WARNING_DROP) severity = 'medium';
  else if (drop > 0.02) severity = 'low';
  return { metric: 'quality_pass_rate_simulated', baseline_pass_rate: pb, current_pass_rate: pc, drop, z,
    survives_bonferroni: T.Z_BONFERRONI != null ? drop > 0 && Math.abs(z) >= T.Z_BONFERRONI : undefined, severity, alert: severity === 'medium' || severity === 'high' };
}

export const METRICS = ['latency_ms', 'total_tokens', 'cost_usd'];

export function detectDrift(base, cur, T, bins = 10) {
  const per = {};
  for (const f of METRICS) per[f] = assessNumeric(f, base.map((r) => r[f]), cur.map((r) => r[f]), T, bins);
  per.quality_pass_rate_simulated = assessPassRate(base, cur, T);
  const alerts = Object.entries(per).filter(([, r]) => r.alert).map(([metric, r]) => ({ metric, severity: r.severity }));
  let overall = 'none';
  for (const r of Object.values(per)) if (SEV.indexOf(r.severity) > SEV.indexOf(overall)) overall = r.severity;
  return { per_metric: per, alerts, alert_count: alerts.length, overall_severity: overall, has_alert: alerts.length > 0 };
}

// run_deep.generate_window, same draw order: gauss latency, gauss tokens, uniform cost, random pass.
export function generateWindow(seed, { latencyMean, tokensMean, costPerToken, passRate, n = 1000, latencySd = 80, tokensSd = 300 }) {
  const rng = new PyRandom(seed);
  const out = new Array(n);
  for (let k = 0; k < n; k++) {
    const latency = Math.max(10, rng.gauss(latencyMean, latencySd));
    const tokens = Math.max(10, roundHalfEven(rng.gauss(tokensMean, tokensSd)));
    const cost = pyRound(tokens * costPerToken * rng.uniform(0.9, 1.1), 6);
    out[k] = { latency_ms: pyRound(latency, 3), total_tokens: tokens, cost_usd: cost, quality_pass: rng.random() < passRate };
  }
  return out;
}

// Wilson score interval for a rate, used to put uncertainty on simulated rates.
export function wilson(k, n, z = 1.959964) {
  if (!n) return [0, 0];
  const p = k / n, d = 1 + (z * z) / n;
  const c = (p + (z * z) / (2 * n)) / d, h = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / d;
  return [Math.max(0, c - h), Math.min(1, c + h)];
}

// calibrate.py's loop: repetition r compares seed seedBase + 2r (baseline) with seedBase + 2r + 1 (current).
export function calibrate({ sizes, reps, seedBase, base, latencyShift = 0, passRate = base.passRate, bins = 10 }, T) {
  return sizes.map((n) => {
    const row = { n, runs: reps, any: 0, latency: 0, ks: 0, pass: 0, bonf: 0, per: Object.fromEntries([...METRICS, 'quality_pass_rate_simulated'].map((m) => [m, 0])) };
    for (let r = 0; r < reps; r++) {
      const b = generateWindow(seedBase + 2 * r, { ...base, n });
      const c = generateWindow(seedBase + 2 * r + 1, { ...base, n, latencyMean: base.latencyMean + latencyShift, passRate });
      const rep = detectDrift(b, c, T, bins);
      row.any += rep.has_alert;
      for (const m in row.per) row.per[m] += rep.per_metric[m].alert;
      row.latency += rep.per_metric.latency_ms.alert;
      row.ks += rep.per_metric.latency_ms.ks_reject;
      row.pass += rep.per_metric.quality_pass_rate_simulated.alert;
      row.bonf += !!rep.per_metric.quality_pass_rate_simulated.survives_bonferroni;
    }
    return row;
  });
}

// The windows in run_deep.build_experiment, parsed from its source: name -> seed and parameters.
export function parseWindows(src) {
  const out = {};
  for (const m of src.matchAll(/(\w+) = generate_window\((\d+), ([\d.]+), ([\d.]+), ([\d.]+), ([\d.]+)\)/g))
    out[m[1]] = { seed: +m[2], latencyMean: +m[3], tokensMean: +m[4], costPerToken: +m[5], passRate: +m[6] };
  if (!out.baseline) throw new Error('baseline window not found in run_deep.py');
  return out;
}
