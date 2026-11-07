// Known-answer check, run by npm run build: the browser port of drift.py + run_deep.py
// must reproduce level-3-deep/results_deep.json and results_calibration.json exactly.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { parseThresholds, parseWindows, generateWindow, detectDrift, calibrate } from './drift.js';

const read = (p) => fs.readFileSync(new URL(`../../${p}`, import.meta.url), 'utf8');
const deep = JSON.parse(read('level-3-deep/results_deep.json'));
const cal = JSON.parse(read('level-3-deep/results_calibration.json'));
const T = { ...parseThresholds(read('level-3-deep/drift.py')), Z_BONFERRONI: deep.windows.control_no_drift.per_metric.quality_pass_rate_simulated.z_bonferroni_threshold };
assert.equal(T.PSI_ALERT, deep.windows.control_no_drift.per_metric.latency_ms.psi_alert_threshold);

const src = read('level-3-deep/run_deep.py');
const calls = parseWindows(src);
const win = (k) => generateWindow(calls[k].seed, { ...calls[k], n: deep.n_per_window });
const base = win('baseline');
const map = { control_no_drift: 'control', latency_cost_drift: 'latency_cost', quality_drift: 'quality' };
let compared = 0;
for (const [name, key] of Object.entries(map)) {
  assert.equal(calls[key].seed, deep.seeds[name]);
  const got = detectDrift(base, win(key), T);
  const want = deep.windows[name];
  assert.equal(got.overall_severity, want.overall_severity, name);
  assert.equal(got.alert_count, want.alert_count, name);
  for (const [m, w] of Object.entries(want.per_metric))
    for (const [f, v] of Object.entries(got.per_metric[m])) {
      if (!(f in w) || v === undefined) continue;
      if (typeof v === 'number') assert.ok(Math.abs(v - w[f]) <= 1e-6, `${name}.${m}.${f}: ${v} vs ${w[f]}`);
      else assert.equal(v, w[f], `${name}.${m}.${f}`);
      compared++;
    }
}

const seedBase = +read('level-3-deep/calibrate.py').match(/^SEED_BASE = (\d+)/m)[1];
const bp = cal.baseline_params;
const B = { latencyMean: bp.latency_mean, tokensMean: bp.tokens_mean, costPerToken: bp.cost_per_token, passRate: bp.pass_rate };
const fa = calibrate({ sizes: cal.false_alert.map((r) => r.n), reps: cal.reps, seedBase, base: B, bins: cal.bins }, T);
fa.forEach((row, i) => {
  assert.equal(row.any, cal.false_alert[i].any_alert, `false alerts at n=${row.n}`);
  assert.deepEqual(row.per, cal.false_alert[i].per_metric_alerts, `per-metric false alerts at n=${row.n}`);
});
for (const s of cal.power.latency_shift) {
  const [r] = calibrate({ sizes: [cal.power.n], reps: cal.reps, seedBase, base: B, latencyShift: s.shift_ms }, T);
  assert.equal(r.latency, s.rule.count, `latency rule at +${s.shift_ms}`);
  assert.equal(r.ks, s.ks.count, `KS at +${s.shift_ms}`);
}
for (const s of cal.power.pass_rate_drop) {
  const [r] = calibrate({ sizes: [cal.power.n], reps: cal.reps, seedBase, base: B, passRate: s.pass_rate }, T);
  assert.equal(r.pass, s.rule.count, `pass rule at ${s.pass_rate}`);
  assert.equal(r.bonf, s.bonferroni.count, `bonferroni at ${s.pass_rate}`);
}
console.log('drift ok', { fieldsCompared: compared, falseAlerts: fa.map((r) => `${r.n}:${r.any}/${r.runs}`).join(' ') });
