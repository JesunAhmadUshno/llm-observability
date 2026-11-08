import { useMemo, useState, useEffect, useCallback, useId } from 'react';
import deep from '../../level-3-deep/results_deep.json';
import cal from '../../level-3-deep/results_calibration.json';
import learn from '../../level-1-learn/results_learn.json';
import build from '../../level-2-build/results_build.json';
import driftSrc from '../../level-3-deep/drift.py?raw';
import runDeepSrc from '../../level-3-deep/run_deep.py?raw';
import calSrc from '../../level-3-deep/calibrate.py?raw';
import obsSrc from '../../level-1-learn/observability.py?raw';
import runBuildSrc from '../../level-2-build/run_build.py?raw';
import storeText from '../../level-2-build/store_build.jsonl?raw';
import { parseThresholds, parseWindows, generateWindow, detectDrift, calibrate, wilson, METRICS } from './drift.js';
import { parsePriceTable, computeCost, percentile, summarize, parseStore, parsePrompts, diffLines, countTests } from './obs.js';

const REPO = 'https://github.com/JesunAhmadUshno/llm-observability';
const blob = (p) => `${REPO}/blob/main/${p}`;
const pct = (x, d = 0) => `${(x * 100).toFixed(d)}%`;
const fmt = (n, d = 0) => Number(n).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
const usd = (x) => `$${x.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: x < 1 ? 6 : 2 })}`;
const minus = (s) => String(s).replace('-', '−');

// Everything below is parsed from repo files at build time.
const T = { ...parseThresholds(driftSrc), Z_BONFERRONI: deep.windows.control_no_drift.per_metric.quality_pass_rate_simulated.z_bonferroni_threshold };
const WINDOWS = parseWindows(runDeepSrc);
const BASE = WINDOWS.baseline;
const SEED_BASE = +calSrc.match(/^SEED_BASE = (\d+)/m)[1];
const PRICES = parsePriceTable(obsSrc);
const STORE = parseStore(storeText);
const PROMPTS = parsePrompts(runBuildSrc);
const TEST_COUNT = countTests(Object.values(import.meta.glob('../../tests/*.py', { query: '?raw', import: 'default', eager: true })));
const PRESETS = [['control_no_drift', 'control', 'No drift (control)'], ['latency_cost_drift', 'latency_cost', 'Latency + cost drift'], ['quality_drift', 'quality', 'Quality drift']];
const METRIC_LABEL = { latency_ms: 'Latency (ms)', total_tokens: 'Total tokens', cost_usd: 'Cost (USD)', quality_pass_rate_simulated: 'Pass rate (simulated)' };
const SEV_PILL = { none: 'good', low: 'info', medium: 'warn', high: 'bad' };

const SECTIONS = [['top', 'Overview', '◎'], ['lab', 'Drift Lab', '≈'], ['calibration', 'Calibration', '◷'], ['report', 'Recorded report', '▥'], ['traces', 'Traces', '⇶'], ['cost', 'Cost', '$'], ['registry', 'Registry', '±'], ['method', 'Method', '❯_']];

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) { els.forEach((e) => e.classList.add('in')); return; }
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.08 });
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
  }, []);
}

function useTheme() {
  const [theme, setTheme] = useState(() => { try { return localStorage.getItem('theme'); } catch { return null; } });
  useEffect(() => {
    if (theme) document.documentElement.dataset.theme = theme; else delete document.documentElement.dataset.theme;
    try { theme ? localStorage.setItem('theme', theme) : localStorage.removeItem('theme'); } catch { /* storage blocked */ }
  }, [theme]);
  const dark = theme ? theme === 'dark' : typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: dark)').matches;
  return [dark, () => setTheme(dark ? 'light' : 'dark')];
}

function MenuBar() {
  const [now, setNow] = useState(() => new Date());
  const [dark, toggle] = useTheme();
  useEffect(() => { const t = setInterval(() => setNow(new Date()), 30000); return () => clearInterval(t); }, []);
  return (
    <div className="menubar" role="banner">
      <span className="apple" aria-hidden="true">◆</span>
      <a className="app" href="#top">LLM Observability</a>
      <a className="m" href={blob('PROPOSAL.md')}>Proposal</a>
      <a className="m" href={blob('REPORT.md')}>Report</a>
      <span className="spacer" />
      <span className="status"><i /> Simulated traffic only</span>
      <button className="theme" onClick={toggle} aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}>{dark ? '☀' : '☾'}</button>
      <a href={REPO}>GitHub ↗</a>
      <span className="clock">{now.toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' })}</span>
    </div>
  );
}

function Dock() {
  const [active, setActive] = useState('top');
  useEffect(() => {
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && setActive(e.target.id)), { rootMargin: '-45% 0px -50% 0px' });
    SECTIONS.forEach(([id]) => { const el = document.getElementById(id); if (el) io.observe(el); });
    return () => io.disconnect();
  }, []);
  return (
    <nav className="dock" aria-label="Sections">
      {SECTIONS.map(([id, label, icon]) => (
        <a key={id} href={`#${id}`} className={active === id ? 'on' : ''} aria-current={active === id ? 'true' : undefined}>
          <span className="ico" aria-hidden="true">{icon}</span><span className="lbl">{label}</span>
        </a>
      ))}
    </nav>
  );
}

function Range({ label, value, min, max, step, onChange, show }) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label} <span>{show}</span></label>
      <input id={id} type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(+e.target.value)} />
    </div>
  );
}

const Badge = ({ kind }) => <span className={`badge ${kind}`}>{kind}</span>;
const Sev = ({ s }) => <span className={`pill ${SEV_PILL[s]}`}>{s}</span>;

export default function App() {
  useReveal();
  return (
    <div className="wrap">
      <MenuBar />
      <div className="glow" aria-hidden="true" />
      <Hero />
      <DriftLab />
      <Calibration />
      <Report />
      <Traces />
      <Cost />
      <Registry />
      <Method />
      <Dock />
      <footer>
        Code: Apache-2.0. Every number on this page is read at build time from the repo’s <code>level-*/</code> result files, store and source;
        the Drift Lab, calibration and calculators re-run the repo’s own code ported to JavaScript in your browser. All traffic is simulated: no real LLM was called.
      </footer>
    </div>
  );
}

function Hero() {
  const w = deep.windows;
  const lat = w.latency_cost_drift.per_metric.latency_ms;
  const q = w.quality_drift.per_metric.quality_pass_rate_simulated;
  const fa = cal.false_alert;
  const first = fa[0], quiet = fa.find((r) => r.any_alert === 0);
  return (
    <header className="card hero window" id="top" data-title="drift.py — llm-observability">
      <div className="head">
        <p className="eyebrow">Verdict: Functional, not pre-registered · simulated traffic only</p>
        <span className={`pill ${deep.success_criteria.all_passed ? 'good' : 'bad'}`}>● Success criteria {deep.success_criteria.all_passed ? 'all passed' : 'failed'}</span>
      </div>
      <h1>On {fmt(deep.n_per_window)}-record seeded windows, the detector <em>caught both injected drifts</em> and stayed quiet on the control.</h1>
      <p className="sub">
        A stdlib Python toolkit for LLM request logging, tracing, a version registry and drift detection.
        The no-drift control raised {w.control_no_drift.alert_count} alerts; latency PSI reached {lat.psi.toFixed(2)}, and a simulated pass rate fell from {q.baseline_pass_rate} to {q.current_pass_rate} (z {minus(q.z.toFixed(1))}).
        Repeated over {cal.reps} seed pairs, the same detector false-alarms on {first.any_alert}/{first.runs} controls at {first.n} records and on {quiet.any_alert}/{quiet.runs} from {quiet.n} up, so window size matters as much as the thresholds.
      </p>
      <div className="actions">
        <a className="btn primary" href="#lab">Re-run the drift experiment</a>
        <a className="btn ghost" href="#calibration">See the false-alarm study</a>
        <span className="hint">Reproduce with <code>python3 level-3-deep/run_deep.py</code></span>
      </div>
      <div className="tiles">
        <div className="tile"><div className="num">{w.control_no_drift.alert_count}</div><div className="cap">Alerts on the no-drift control <Badge kind="simulated" /></div></div>
        <div className="tile"><div className="num">{lat.psi.toFixed(2)}</div><div className="cap">Latency PSI under injected drift (alert at {T.PSI_ALERT}) <Badge kind="simulated" /></div></div>
        <div className="tile"><div className="num">{q.current_pass_rate}</div><div className="cap">Simulated pass rate under quality drift, down from {q.baseline_pass_rate} <Badge kind="simulated" /></div></div>
        <div className="tile"><div className="num">{minus(q.z.toFixed(1))}</div><div className="cap">Two-proportion z (alert at |z| ≥ {T.Z_ALERT}) <Badge kind="simulated" /></div></div>
      </div>
      <div className="facts">
        <span className="pill info">{learn.summary.count} Learn requests <Badge kind="simulated" /></span>
        <span className="pill info">{build.summary.count} Build requests, {build.span_count} spans <Badge kind="simulated" /></span>
        <span className="pill info">{TEST_COUNT} unit tests in tests/</span>
        <span className="pill info">Prices: teaching constants</span>
      </div>
    </header>
  );
}

function Histogram({ base, cur, label }) {
  const W = 960, H = 220, pad = { l: 12, r: 12, t: 14, b: 26 }, NB = 48;
  const all = [...base, ...cur];
  let lo = Infinity, hi = -Infinity;
  for (const v of all) { if (v < lo) lo = v; if (v > hi) hi = v; }
  if (hi === lo) hi = lo + 1;
  const bin = (xs) => { const c = new Array(NB).fill(0); for (const v of xs) c[Math.min(NB - 1, Math.floor(((v - lo) / (hi - lo)) * NB))]++; return c; };
  const cb = bin(base), cc = bin(cur), top = Math.max(...cb, ...cc);
  const x = (i) => pad.l + (i / NB) * (W - pad.l - pad.r);
  const y = (c) => pad.t + (1 - c / top) * (H - pad.t - pad.b);
  const sorted = [...base].sort((a, b) => a - b);
  const edges = Array.from({ length: 9 }, (_, i) => sorted[Math.round(((i + 1) * sorted.length) / 10) - 1]);
  const path = (c) => `M${x(0)},${y(0)} ` + c.map((v, i) => `L${x(i)},${y(v)} L${x(i + 1)},${y(v)}`).join(' ') + ` L${x(NB)},${y(0)} Z`;
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label}>
      {edges.map((e, i) => <line key={i} className="axis" x1={x(((e - lo) / (hi - lo)) * NB)} x2={x(((e - lo) / (hi - lo)) * NB)} y1={pad.t} y2={H - pad.b} strokeDasharray="3 4" />)}
      <path d={path(cb)} fill="var(--muted)" opacity="0.22" />
      <path d={path(cc)} fill="var(--primary)" opacity="0.35" stroke="var(--primary)" strokeWidth="1" />
      <line className="axis" x1={pad.l} x2={W - pad.r} y1={y(0)} y2={y(0)} />
      <text x={pad.l} y={H - 6}>{fmt(lo, 0)} ms</text>
      <text x={W - pad.r} y={H - 6} textAnchor="end">{fmt(hi, 0)} ms</text>
      <text x={W / 2} y={H - 6} textAnchor="middle">dashed lines: the baseline decile edges PSI bins on</text>
    </svg>
  );
}

function DriftLab() {
  const [n, setN] = useState(deep.n_per_window);
  const [lat, setLat] = useState(BASE.latencyMean);
  const [tok, setTok] = useState(BASE.tokensMean);
  const [cpt, setCpt] = useState(BASE.costPerToken);
  const [pass, setPass] = useState(BASE.passRate);
  const [seed, setSeed] = useState(WINDOWS.control.seed);
  const [bins, setBins] = useState(cal.bins);
  const apply = (key) => { const p = WINDOWS[key]; setLat(p.latencyMean); setTok(p.tokensMean); setCpt(p.costPerToken); setPass(p.passRate); setSeed(p.seed); setN(deep.n_per_window); setBins(cal.bins); };
  const { report, base, cur, ms } = useMemo(() => {
    const t0 = performance.now();
    const b = generateWindow(BASE.seed, { ...BASE, n });
    const c = generateWindow(seed, { latencyMean: lat, tokensMean: tok, costPerToken: cpt, passRate: pass, n });
    return { report: detectDrift(b, c, T, bins), base: b, cur: c, ms: performance.now() - t0 };
  }, [n, lat, tok, cpt, pass, seed, bins]);
  const preset = PRESETS.find(([, key]) => { const p = WINDOWS[key]; return p.seed === seed && p.latencyMean === lat && p.tokensMean === tok && p.costPerToken === cpt && p.passRate === pass; });
  const atRecorded = preset && n === deep.n_per_window && bins === cal.bins;
  let match = null;
  if (atRecorded) {
    const want = deep.windows[preset[0]].per_metric;
    match = Object.entries(want).every(([m, w]) => ['psi', 'mean_shift_pooled_sd', 'z', 'baseline_mean', 'current_mean', 'ks_statistic'].every((f) => !(f in w) || Math.abs(report.per_metric[m][f] - w[f]) <= 1e-6));
  }
  const pr = report.per_metric.quality_pass_rate_simulated;
  return (
    <section id="lab" className="card window reveal" data-title="run_deep.py — live in your browser">
      <div className="head">
        <div>
          <p className="eyebrow">Drift Lab · live</p>
          <h2>Inject drift into a window and watch <em>which statistic</em> notices.</h2>
          <p className="sub">
            This is run_deep.py’s generator and drift.py’s detector ported to JavaScript, including an exact port of Python’s Mersenne Twister, so the baseline window (seed {BASE.seed}) is the same {fmt(n)} records Python draws.
            Pick a recorded window to reproduce results_deep.json, or move the sliders to build your own drift. Thresholds are parsed from drift.py: PSI {T.PSI_WARNING} / {T.PSI_ALERT}, mean shift {T.MEAN_SHIFT_WARNING} / {T.MEAN_SHIFT_ALERT} SD, pass-rate drop {T.PASS_RATE_WARNING_DROP} / {T.PASS_RATE_ALERT_DROP} with |z| ≥ {T.Z_ALERT}.
          </p>
        </div>
        <span className="pill info">2 × {fmt(n)} records in {ms.toFixed(0)} ms</span>
      </div>
      <div className="seg wrapseg" role="group" aria-label="Recorded windows">
        {PRESETS.map(([name, key, label]) => <button key={name} aria-pressed={preset?.[0] === name} onClick={() => apply(key)}>{label}</button>)}
      </div>
      <div className="controls" style={{ marginTop: 16 }}>
        <Range label="Window size (records)" value={n} min={100} max={3000} step={100} onChange={setN} show={fmt(n)} />
        <Range label="Current latency mean" value={lat} min={300} max={1000} step={5} onChange={setLat} show={`${lat} ms`} />
        <Range label="Current tokens mean" value={tok} min={800} max={3000} step={20} onChange={setTok} show={fmt(tok)} />
        <Range label="Cost per token" value={cpt} min={0.0003} max={0.0012} step={0.0001} onChange={(v) => setCpt(+v.toFixed(4))} show={`$${cpt.toFixed(4)}`} />
        <Range label="Simulated pass rate" value={pass} min={0.5} max={0.99} step={0.01} onChange={(v) => setPass(+v.toFixed(2))} show={pass.toFixed(2)} />
        <Range label="PSI bins" value={bins} min={3} max={20} step={1} onChange={setBins} show={bins} />
        <div className="field"><label htmlFor="lab-seed">Current window seed</label><input id="lab-seed" type="number" value={seed} onChange={(e) => setSeed(Math.max(0, Math.floor(+e.target.value || 0)))} /></div>
      </div>
      <div className="labstatus">
        <span className={`pill ${report.has_alert ? SEV_PILL[report.overall_severity] : 'good'}`}>Overall: {report.overall_severity}, {report.alert_count} alert{report.alert_count === 1 ? '' : 's'}</span>
        {atRecorded ? <span className={`pill ${match ? 'good' : 'bad'}`}>{match ? `✓ Matches results_deep.json (${preset[0]}) to 6 dp` : '✗ Differs from results_deep.json'}</span>
          : <span className="hint">Live browser simulation over the repo’s generator, not a recorded result. Choose a recorded window above to compare with results_deep.json.</span>}
      </div>
      <div style={{ overflowX: 'auto', marginTop: 12 }}>
        <table>
          <thead><tr><th>Metric</th><th>Baseline → current</th><th>PSI</th><th>Mean shift (SD)</th><th>KS D (crit, α {T.KS_FAMILY_ALPHA}/3)</th><th>Severity</th></tr></thead>
          <tbody>
            {METRICS.map((m) => { const r = report.per_metric[m]; return (
              <tr key={m}><td>{METRIC_LABEL[m]}</td><td>{fmt(r.baseline_mean, m === 'cost_usd' ? 4 : 1)} → {fmt(r.current_mean, m === 'cost_usd' ? 4 : 1)}</td>
                <td className={r.psi >= T.PSI_ALERT ? 'no' : ''}>{r.psi.toFixed(4)}</td><td>{Number.isFinite(r.mean_shift_pooled_sd) ? r.mean_shift_pooled_sd.toFixed(3) : '∞'}</td>
                <td className={r.ks_reject ? 'no' : ''}>{r.ks_statistic.toFixed(3)} ({r.ks_critical_bonferroni.toFixed(3)})</td><td><Sev s={r.severity} /></td></tr>); })}
            <tr><td>{METRIC_LABEL.quality_pass_rate_simulated}</td><td>{pr.baseline_pass_rate.toFixed(3)} → {pr.current_pass_rate.toFixed(3)}</td><td colSpan="3">drop {minus(pr.drop.toFixed(3))}, z {minus(pr.z.toFixed(3))}{pr.survives_bonferroni ? `, survives Bonferroni (|z| ≥ ${T.Z_BONFERRONI.toFixed(2)})` : ''}</td><td><Sev s={pr.severity} /></td></tr>
          </tbody>
        </table>
      </div>
      <h3 style={{ marginTop: 20 }}>Latency distribution: baseline (grey) vs current (blue)</h3>
      <Histogram base={base.map((r) => r.latency_ms)} cur={cur.map((r) => r.latency_ms)} label="Latency histogram of the baseline window versus the current window" />
      <p className="hint">KS is reported as a distribution-free baseline and does not set severity. It often fires on shifts PSI rates as none: compare the quality-drift window’s latency row.</p>
    </section>
  );
}

function Calibration() {
  const sizes = cal.false_alert.map((r) => r.n);
  const [reps, setReps] = useState(cal.reps);
  const [bins, setBins] = useState(cal.bins);
  const [shift, setShift] = useState(0);
  const [pass, setPass] = useState(BASE.passRate);
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  const run = useCallback(() => {
    setBusy(true);
    requestAnimationFrame(() => setTimeout(() => {
      const t0 = performance.now();
      const rows = calibrate({ sizes, reps, seedBase: SEED_BASE, base: BASE, latencyShift: shift, passRate: pass, bins }, T);
      setRes({ rows, ms: performance.now() - t0, drift: shift !== 0 || pass !== BASE.passRate, recorded: reps === cal.reps && bins === cal.bins && shift === 0 && pass === BASE.passRate });
      setBusy(false);
    }, 0));
  }, [reps, bins, shift, pass]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { run(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const W = 960, H = 260, pad = { l: 44, r: 40, t: 14, b: 30 };
  const x = (i) => pad.l + (i / (sizes.length - 1)) * (W - pad.l - pad.r);
  const y = (v) => pad.t + (1 - v) * (H - pad.t - pad.b);
  const band = res && res.rows.map((r) => wilson(r.any, r.runs));
  const p = cal.power, cu = cal.cusum_latency;
  return (
    <section id="calibration" className="card window reveal" data-title="calibrate.py — false alarms and power">
      <div className="head">
        <div>
          <p className="eyebrow">Calibration · live + recorded</p>
          <h2>How often does it <em>cry wolf</em>? It depends on the window size.</h2>
          <p className="sub">
            run_deep.py uses one seed per window, which shows the detector working once. calibrate.py repeats the comparison over {cal.reps} independent seed pairs per window size.
            The dots are its recorded false-alert rates on the no-drift control; the line is your browser re-running the same loop (seed {SEED_BASE} + 2r vs {SEED_BASE} + 2r + 1) with your settings. Add drift to turn the false-alert curve into a detection curve.
          </p>
        </div>
        <span className="pill info">{res ? `${fmt(res.rows.reduce((a, r) => a + r.runs * r.n * 2, 0))} records in ${res.ms.toFixed(0)} ms` : 'running…'}</span>
      </div>
      <div className="controls">
        <Range label="Seed pairs per size" value={reps} min={10} max={100} step={10} onChange={setReps} show={reps} />
        <Range label="PSI bins" value={bins} min={3} max={20} step={1} onChange={setBins} show={bins} />
        <Range label="Latency shift" value={shift} min={0} max={80} step={5} onChange={setShift} show={shift ? `+${shift} ms` : 'none'} />
        <Range label="Simulated pass rate" value={pass} min={0.8} max={0.92} step={0.01} onChange={(v) => setPass(+v.toFixed(2))} show={pass === BASE.passRate ? `${pass} (no drift)` : pass.toFixed(2)} />
      </div>
      <div className="actions" style={{ marginTop: 0, marginBottom: 16 }}>
        <button className="btn primary" onClick={run} disabled={busy}>{busy ? 'Simulating…' : 'Run calibration'}</button>
        <span className="hint">{res?.recorded ? 'At the recorded settings the live line must sit on the recorded dots (checked at build time).' : 'Live browser simulation over the repo’s generator, not a recorded result.'}</span>
      </div>
      <div className="chart-scroll" style={{ overflowX: 'auto' }}>
      <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Alert rate versus window size: recorded false-alert rate and live browser recompute">
        {[0, 0.25, 0.5, 0.75, 1].map((t) => <g key={t}><line className="axis" x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} /><text x={pad.l - 8} y={y(t) + 4} textAnchor="end">{pct(t)}</text></g>)}
        {sizes.map((s, i) => <text key={s} x={x(i)} y={H - 8} textAnchor="middle">N = {fmt(s)}</text>)}
        {res && <path d={`M${band.map((b, i) => `${x(i)},${y(b[1])}`).join(' L')} L${band.map((b, i) => [i, b]).reverse().map(([i, b]) => `${x(i)},${y(b[0])}`).join(' L')} Z`} fill="var(--primary)" opacity="0.12" />}
        {res && <polyline fill="none" stroke="var(--primary)" strokeWidth="2.5" points={res.rows.map((r, i) => `${x(i)},${y(r.any / r.runs)}`).join(' ')} />}
        {res && res.rows.map((r, i) => <circle key={r.n} cx={x(i)} cy={y(r.any / r.runs)} r="4" fill="var(--primary)" />)}
        {cal.false_alert.map((r, i) => <rect key={r.n} x={x(i) - 6} y={y(r.any_alert_rate) - 6} width="12" height="12" fill="none" stroke="var(--text)" strokeWidth="2" transform={`rotate(45 ${x(i)} ${y(r.any_alert_rate)})`} />)}
      </svg>
      </div>
      <div className="legend"><span><i style={{ background: 'var(--primary)' }} />Live: {res?.drift ? 'detection' : 'false-alert'} rate, any metric, with Wilson 95% band</span><span><i style={{ border: '2px solid var(--text)', background: 'transparent' }} />Recorded: false-alert rate, results_calibration.json</span></div>
      {res && (
        <div style={{ overflowX: 'auto', marginTop: 12 }}>
          <table>
            <thead><tr><th>Window size</th><th>Any alert</th>{[...METRICS, 'quality_pass_rate_simulated'].map((m) => <th key={m}>{METRIC_LABEL[m]}</th>)}<th>Recorded (control)</th></tr></thead>
            <tbody>{res.rows.map((r, i) => <tr key={r.n}><td>{fmt(r.n)}</td><td><b>{r.any}/{r.runs}</b></td>{Object.values(r.per).map((v, j) => <td key={j}>{v}</td>)}<td>{cal.false_alert[i].any_alert}/{cal.false_alert[i].runs}</td></tr>)}</tbody>
          </table>
        </div>
      )}
      <div className="grid2" style={{ marginTop: 24 }}>
        <div>
          <h3>Recorded power at N = {fmt(p.n)}: latency shift <Badge kind="recorded" /></h3>
          <PowerBars rows={p.latency_shift.map((r) => ({ k: `+${r.shift_ms} ms (${r.shift_sd} SD)`, a: r.rule, b: r.ks }))} la="PSI / mean-shift rule" lb="KS (Bonferroni)" label="Detection rate by latency shift: PSI and mean-shift rule versus KS" />
        </div>
        <div>
          <h3>Recorded power at N = {fmt(p.n)}: pass-rate drop <Badge kind="recorded" /></h3>
          <PowerBars rows={p.pass_rate_drop.map((r) => ({ k: `${BASE.passRate} → ${r.pass_rate}`, a: r.rule, b: r.bonferroni }))} la="drop + z rule" lb="z alone, Bonferroni" label="Detection rate by simulated pass-rate drop: drop rule versus Bonferroni z" />
        </div>
      </div>
      <div className="tiles" style={{ marginTop: 20 }}>
        <div className="tile"><div className="num">{cu.false_alarm_before_change.count}/{cu.runs}</div><div className="cap">CUSUM streams that alarmed before the change ({cu.pre_change_records} clean records, h {cu.h_sd} SD) <Badge kind="recorded" /></div></div>
        <div className="tile"><div className="num">{cu.delay_records_median}</div><div className="cap">Median records to detect a +{cu.shift_ms} ms step ({cu.delay_records_min} to {cu.delay_records_max}, {cu.detected} detected) <Badge kind="recorded" /></div></div>
        <div className="tile"><div className="num">{p.latency_shift.find((r) => r.ks.rate === 1).shift_ms} ms</div><div className="cap">Smallest shift KS caught in every run; the PSI rule needed {p.latency_shift.find((r) => r.rule.rate === 1).shift_ms} ms <Badge kind="recorded" /></div></div>
        <div className="tile"><div className="num">{T.PASS_RATE_ALERT_DROP}</div><div className="cap">Drop for a high alert; the rule’s medium tier (drop ≥ {T.PASS_RATE_WARNING_DROP}) fires earlier</div></div>
      </div>
    </section>
  );
}

function PowerBars({ rows, la, lb, label }) {
  return (
    <div className="bars" style={{ marginTop: 12 }} role="img" aria-label={label}>
      {rows.map((r) => (
        <div className="bar-row" key={r.k}>
          <div className="lab"><span>{r.k}</span><b>{pct(r.a.rate)} · {pct(r.b.rate)}</b></div>
          <div className="track duo"><div className="fill" style={{ width: pct(r.a.rate), background: 'var(--primary)' }} /></div>
          <div className="track duo"><div className="fill" style={{ width: pct(r.b.rate), background: 'var(--warn)' }} /></div>
        </div>
      ))}
      <div className="legend"><span><i style={{ background: 'var(--primary)' }} />{la}</span><span><i style={{ background: 'var(--warn)' }} />{lb}</span><span>{rows[0].a.runs} runs each</span></div>
    </div>
  );
}

function Report() {
  const [stat, setStat] = useState('psi');
  const [hover, setHover] = useState(null);
  const rows = PRESETS.flatMap(([name, , label]) => METRICS.map((m) => ({ name, label, m, r: deep.windows[name].per_metric[m] })));
  const W = 960, rowH = 26, l = 300, r = 70, H = rows.length * rowH + 34;
  const isPsi = stat === 'psi';
  const lo = isPsi ? 1e-3 : 1e-2, hi = isPsi ? 10 : 1;
  const x = (v) => l + ((Math.log10(Math.max(lo, Math.min(hi, v))) - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo))) * (W - l - r);
  const ticks = isPsi ? [0.001, 0.01, 0.1, 1, 10] : [0.01, 0.1, 1];
  const val = (row) => (isPsi ? row.r.psi : row.r.ks_statistic);
  return (
    <section id="report" className="card window reveal" data-title="results_deep.json — recorded">
      <div className="head">
        <div>
          <p className="eyebrow">Recorded drift report <Badge kind="recorded" /></p>
          <h2>Three recorded windows against the <em>{T.PSI_WARNING} / {T.PSI_ALERT}</em> PSI bands.</h2>
          <p className="sub">
            Exactly what run_deep.py wrote: baseline seed {deep.seeds.baseline} ({deep.baseline_params.latency_mean_ms} ms latency, {fmt(deep.baseline_params.tokens_mean)} tokens, ${deep.baseline_params.cost_per_token} per token, pass rate {deep.baseline_params.pass_rate}) against controls with seeds {deep.seeds.control_no_drift}, {deep.seeds.latency_cost_drift} and {deep.seeds.quality_drift}, {fmt(deep.n_per_window)} records each. Log scale.
          </p>
        </div>
        <div className="seg" role="group" aria-label="Statistic">
          {[['psi', 'PSI'], ['ks', 'KS D']].map(([k, t]) => <button key={k} aria-pressed={stat === k} onClick={() => setStat(k)}>{t}</button>)}
        </div>
      </div>
      <div className="chart-scroll" style={{ overflowX: 'auto' }}>
      <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Recorded ${isPsi ? 'PSI' : 'KS statistic'} per window and metric, log scale`} onMouseLeave={() => setHover(null)}>
        {isPsi && <><rect x={x(T.PSI_WARNING)} width={x(T.PSI_ALERT) - x(T.PSI_WARNING)} y={0} height={H - 26} fill="var(--warn)" opacity="0.1" /><rect x={x(T.PSI_ALERT)} width={W - r - x(T.PSI_ALERT)} y={0} height={H - 26} fill="var(--bad)" opacity="0.08" /></>}
        {ticks.map((t) => <g key={t}><line className="axis" x1={x(t)} x2={x(t)} y1={0} y2={H - 26} /><text x={x(t)} y={H - 8} textAnchor="middle">{t}</text></g>)}
        {rows.map((row, i) => {
          const v = val(row), c = isPsi ? `var(--${SEV_PILL[row.r.severity] === 'good' ? 'good' : SEV_PILL[row.r.severity]})` : row.r.ks_reject ? 'var(--bad)' : 'var(--good)';
          const yy = i * rowH + 14;
          return (
            <g key={`${row.name}-${row.m}`} onMouseEnter={() => setHover(row)} opacity={hover && hover !== row ? 0.45 : 1}>
              <text x={0} y={yy + 4} style={{ fill: 'var(--text)', fontSize: 12.5 }}>{row.m === 'latency_ms' ? row.label : ''}</text>
              <text x={l - 10} y={yy + 4} textAnchor="end">{METRIC_LABEL[row.m]}</text>
              <rect x={l} y={yy - 7} width={Math.max(2, x(v) - l)} height={14} rx="4" fill={c} opacity="0.85" />
              <text x={x(v) + 6} y={yy + 4} style={{ fill: 'var(--text)' }}>{v.toFixed(isPsi ? 4 : 3)}</text>
            </g>
          );
        })}
      </svg>
      </div>
      <div className="tip" aria-live="polite">
        {hover ? <>{hover.label}, {METRIC_LABEL[hover.m]}: PSI {hover.r.psi}, mean shift {hover.r.mean_shift_pooled_sd} SD, KS D {hover.r.ks_statistic} (critical {hover.r.ks_critical_bonferroni}), severity {hover.r.severity}</> : 'Hover a bar for the recorded values. Bars are coloured by severity (PSI) or by KS rejection.'}
      </div>
      <div style={{ overflowX: 'auto', marginTop: 12 }}>
        <table>
          <thead><tr><th>Window</th><th>Simulated pass rate</th><th>Drop</th><th>z</th><th>Severity</th><th>Overall</th><th>Alerts</th></tr></thead>
          <tbody>{PRESETS.map(([name, , label]) => { const w = deep.windows[name], q = w.per_metric.quality_pass_rate_simulated; return (
            <tr key={name}><td>{label}</td><td>{q.baseline_pass_rate} → {q.current_pass_rate}</td><td>{minus(q.drop)}</td><td>{minus(q.z)}</td><td><Sev s={q.severity} /></td><td><Sev s={w.overall_severity} /></td><td>{w.alert_count}</td></tr>); })}</tbody>
        </table>
      </div>
    </section>
  );
}

function Waterfall({ rec }) {
  const root = rec.spans.find((s) => s.parent_id === null);
  const order = [root, ...rec.spans.filter((s) => s !== root)];
  const W = 480, rowH = 34, l = 150, r = 52, H = order.length * rowH + 28;
  const x = (t) => l + ((t - root.start_ms) / root.duration_ms) * (W - l - r);
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Trace waterfall for request ${rec.request_id}`}>
      {[0, 0.25, 0.5, 0.75, 1].map((f) => <g key={f}><line className="axis" x1={x(root.start_ms + f * root.duration_ms)} x2={x(root.start_ms + f * root.duration_ms)} y1={0} y2={H - 22} /><text x={x(root.start_ms + f * root.duration_ms)} y={H - 6} textAnchor="middle">{Math.round(f * root.duration_ms)} ms</text></g>)}
      {order.map((s, i) => (
        <g key={s.span_id} transform={`translate(0 ${i * rowH + 18})`}>
          <text x={s.parent_id ? 18 : 0} y={4} style={{ fill: 'var(--text)', fontSize: 12.5 }}>{s.parent_id ? '└ ' : ''}{s.name}</text>
          <rect x={x(s.start_ms)} y={-9} width={Math.max(2, x(s.end_ms) - x(s.start_ms))} height={18} rx="5" fill={s.parent_id ? (s.name.startsWith('model_call') ? 'var(--primary)' : 'var(--warn)') : 'var(--muted)'} opacity={s.parent_id ? 0.85 : 0.35} />
          <text x={x(s.end_ms) + 6} y={4}>{s.duration_ms} ms</text>
        </g>
      ))}
    </svg>
  );
}

function Traces() {
  const [model, setModel] = useState('all');
  const [pv, setPv] = useState('all');
  const [sel, setSel] = useState(STORE[1].request_id);
  const models = [...new Set(STORE.map((r) => r.model))].sort();
  const versions = [...new Set(STORE.map((r) => r.prompt_version))].sort();
  const rows = STORE.filter((r) => (model === 'all' || r.model === model) && (pv === 'all' || r.prompt_version === pv));
  const s = rows.length ? summarize(rows) : null;
  const rec = STORE.find((r) => r.request_id === sel);
  return (
    <section id="traces" className="card window reveal" data-title="store_build.jsonl — 60 persisted requests">
      <div className="head">
        <div>
          <p className="eyebrow">Request log explorer <Badge kind="recorded" /> <Badge kind="simulated" /></p>
          <h2>Every persisted request, and <em>the trace</em> behind it.</h2>
          <p className="sub">
            A replay of the {STORE.length} records and {STORE.reduce((a, r) => a + r.spans.length, 0)} spans the Build service wrote to store_build.jsonl. Latencies come from fixed tables in run_build.py, and tokens use the stated proxy {build.token_proxy.split(',')[0]}, not a real tokenizer.
            Filter the log; the summary is recomputed live with the repo’s nearest-rank percentile. Click a row to draw its trace.
          </p>
        </div>
      </div>
      <div className="controls">
        <div className="field"><label htmlFor="f-model">Model</label><select id="f-model" value={model} onChange={(e) => setModel(e.target.value)}><option value="all">All models</option>{models.map((m) => <option key={m}>{m}</option>)}</select></div>
        <div className="field"><label htmlFor="f-pv">Prompt version</label><select id="f-pv" value={pv} onChange={(e) => setPv(e.target.value)}><option value="all">All versions</option>{versions.map((v) => <option key={v}>{v}</option>)}</select></div>
      </div>
      {s && (
        <div className="tiles mini">
          <div className="tile"><div className="num">{s.count}</div><div className="cap">requests</div></div>
          <div className="tile"><div className="num">{s.mean_latency_ms}</div><div className="cap">mean latency, ms</div></div>
          <div className="tile"><div className="num">{s.p50_latency_ms} / {s.p95_latency_ms}</div><div className="cap">p50 / p95 latency, ms</div></div>
          <div className="tile"><div className="num">{usd(s.total_cost_usd)}</div><div className="cap">total cost at teaching prices</div></div>
        </div>
      )}
      <div className="grid2" style={{ marginTop: 16 }}>
        <div className="scroll-y" style={{ overflow: 'auto' }}>
          <table className="pick">
            <thead><tr><th>Request</th><th>Model</th><th>Prompt</th><th>Tokens</th><th>Latency</th></tr></thead>
            <tbody>{rows.map((r) => (
              <tr key={r.request_id} className={r.request_id === sel ? 'sel' : ''}>
                <td><button className="rowbtn" onClick={() => setSel(r.request_id)} aria-pressed={r.request_id === sel}>{r.request_id}</button></td>
                <td>{r.model}</td><td>{r.prompt_version}</td><td>{r.total_tokens}</td><td>{r.latency_ms} ms</td>
              </tr>))}</tbody>
          </table>
        </div>
        <div>
          {rec && <>
            <h3>{rec.request_id} · {rec.model} · prompt {rec.prompt_version}</h3>
            <Waterfall rec={rec} />
            <p className="hint" style={{ marginTop: 8 }}><b>Prompt</b> ({rec.prompt_tokens} proxy tokens): {rec.prompt}</p>
            <p className="hint"><b>Completion</b> ({rec.completion_tokens} proxy tokens): {rec.completion_text}</p>
            <p className="hint">Cost {usd(rec.cost_usd)} · sha256 <span className="mono">{rec.prompt_hash.slice(0, 12)}…</span></p>
          </>}
        </div>
      </div>
    </section>
  );
}

function Cost() {
  const models = Object.keys(PRICES);
  const [pt, setPt] = useState(1000);
  const [ct, setCt] = useState(500);
  const [mix, setMix] = useState(0.5);
  const [reqs, setReqs] = useState(10000);
  const [ds, setDs] = useState('learn');
  const [p, setP] = useState(95);
  const per = Object.fromEntries(models.map((m) => [m, computeCost(PRICES, m, pt, ct)]));
  const large = models.find((m) => m.includes('large')) ?? models[models.length - 1];
  const small = models.find((m) => m !== large);
  const blended = (1 - mix) * per[small] + mix * per[large];
  const src = ds === 'learn' ? { recs: learn.records, sum: learn.summary } : { recs: STORE, sum: build.summary };
  const lat = src.recs.map((r) => r.latency_ms);
  const v = percentile(lat, p);
  return (
    <section id="cost" className="card window reveal" data-title="observability.py — compute_cost · percentile">
      <div className="head">
        <div>
          <p className="eyebrow">Cost and latency calculator · live</p>
          <h2>What a request costs at the <em>stated teaching prices</em>.</h2>
          <p className="sub">compute_cost and the nearest-rank percentile, ported from observability.py. The price table is parsed from its source at build time; the build fails unless the port reproduces all {learn.records.length + build.records.length} recorded costs.</p>
        </div>
        <span className="pill warn">Teaching constants, not vendor prices</span>
      </div>
      <div className="grid2">
        <div>
          <div className="controls" style={{ gridTemplateColumns: '1fr' }}>
            <Range label="Prompt tokens per request" value={pt} min={0} max={8000} step={50} onChange={setPt} show={fmt(pt)} />
            <Range label="Completion tokens per request" value={ct} min={0} max={4000} step={50} onChange={setCt} show={fmt(ct)} />
            <Range label={`Share of traffic on ${large}`} value={mix} min={0} max={1} step={0.05} onChange={setMix} show={pct(mix)} />
            <Range label="Requests" value={reqs} min={1000} max={1000000} step={1000} onChange={setReqs} show={fmt(reqs)} />
          </div>
          <table>
            <thead><tr><th>Model</th><th>Input / 1k</th><th>Output / 1k</th><th>Per request</th></tr></thead>
            <tbody>{models.map((m) => <tr key={m}><td className="mono">{m}</td><td>${PRICES[m].input_per_1k.toFixed(2)}</td><td>${PRICES[m].output_per_1k.toFixed(2)}</td><td>{usd(per[m])}</td></tr>)}</tbody>
          </table>
          <div className="tiles" style={{ gridTemplateColumns: '1fr 1fr' }}>
            <div className="tile"><div className="num">{usd(blended)}</div><div className="cap">blended cost per request</div></div>
            <div className="tile"><div className="num">{usd(blended * reqs)}</div><div className="cap">for {fmt(reqs)} requests at this mix</div></div>
          </div>
        </div>
        <div>
          <h3>Nearest-rank percentile over recorded latencies</h3>
          <div className="seg" role="group" aria-label="Latency set" style={{ marginTop: 12 }}>
            {[['learn', `Learn (${learn.records.length})`], ['build', `Build (${STORE.length})`]].map(([k, t]) => <button key={k} aria-pressed={ds === k} onClick={() => setDs(k)}>{t}</button>)}
          </div>
          <div className="controls" style={{ gridTemplateColumns: '1fr', marginTop: 12 }}>
            <Range label="Percentile p" value={p} min={1} max={100} step={1} onChange={setP} show={`p${p}`} />
          </div>
          <LatencyStrip values={lat} mark={v} p={p} />
          <div className="tiles" style={{ gridTemplateColumns: '1fr 1fr' }}>
            <div className="tile"><div className="num">{v} ms</div><div className="cap">p{p}: rank ⌈{p}/100 × {lat.length}⌉ = {Math.max(1, Math.ceil((p / 100) * lat.length))}</div></div>
            <div className="tile"><div className="num">{percentile(lat, 50) === src.sum.p50_latency_ms && percentile(lat, 95) === src.sum.p95_latency_ms ? '✓' : '✗'}</div><div className="cap">live p50 {percentile(lat, 50)} / p95 {percentile(lat, 95)} vs recorded {src.sum.p50_latency_ms} / {src.sum.p95_latency_ms}</div></div>
          </div>
        </div>
      </div>
    </section>
  );
}

function LatencyStrip({ values, mark, p }) {
  const s = [...values].sort((a, b) => a - b);
  const W = 460, H = 90, l = 10, r = 10, lo = s[0], hi = s[s.length - 1] === lo ? lo + 1 : s[s.length - 1];
  const x = (v) => l + ((v - lo) / (hi - lo)) * (W - l - r);
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Sorted latencies with the p${p} value marked`}>
      <line className="axis" x1={l} x2={W - r} y1={44} y2={44} />
      {s.map((v, i) => <circle key={i} cx={x(v)} cy={44 + ((i % 3) - 1) * 8} r="3.5" fill={v <= mark ? 'var(--primary)' : 'var(--muted)'} opacity={v <= mark ? 0.85 : 0.4} />)}
      <line x1={x(mark)} x2={x(mark)} y1={14} y2={70} stroke="var(--text)" strokeWidth="1.5" />
      <text x={x(mark)} y={10} textAnchor={x(mark) > W - 60 ? 'end' : 'middle'} style={{ fill: 'var(--text)' }}>p{p} = {mark} ms</text>
      <text x={l} y={H - 4}>{lo} ms</text><text x={W - r} y={H - 4} textAnchor="end">{hi} ms</text>
    </svg>
  );
}

function Registry() {
  const d = build.registry_diff_prompt_v1_v2;
  const oldL = PROMPTS[d.old_version].lines, newL = PROMPTS[d.new_version].lines;
  const live = diffLines(oldL, newL);
  const byVersion = [d.old_version, d.new_version].map((v) => ({ v, ...summarize(STORE.filter((r) => r.prompt_version === v)) }));
  return (
    <section id="registry" className="card window reveal" data-title={`registry — ${d.name}`}>
      <p className="eyebrow">Version registry <Badge kind="recorded" /></p>
      <h2>Prompt {d.old_version} → {d.new_version}: <em>one line added</em>, logged and diffed.</h2>
      <p className="sub">The two prompt versions registered in run_build.py, diffed line by line in the browser; results_build.json recorded added {d.diff.added.length}, removed {d.diff.removed.length}, unchanged {d.diff.unchanged}, and the build checks the live diff matches.</p>
      <div className="grid2" style={{ marginTop: 16 }}>
        <div>
          <div className="diff" role="group" aria-label={`Diff of ${d.name} ${d.old_version} to ${d.new_version}`}>
            {newL.map((line, i) => <div key={i} className={live.added.includes(line) ? 'add' : 'same'}><span>{live.added.includes(line) ? '+' : ' '}</span>{line}</div>)}
            {live.removed.map((line, i) => <div key={`r${i}`} className="del"><span>−</span>{line}</div>)}
          </div>
          <p className="hint">Recorded diff: added “{d.diff.added.join('”, “')}”; removed {d.diff.removed.length ? d.diff.removed.join(', ') : 'none'}; unchanged {d.diff.unchanged} lines.</p>
        </div>
        <div>
          <h3>Changelog</h3>
          <ol className="steps" style={{ marginTop: 12 }}>
            {build.registry_changelog.map((c, i) => <li key={i}><span className="n">{i + 1}</span><div><b className="mono">{c.kind} · {c.name} · {c.version}</b></div></li>)}
          </ol>
          <h3 style={{ marginTop: 16 }}>Build traffic by prompt version <Badge kind="simulated" /></h3>
          <table><thead><tr><th>Version</th><th>Requests</th><th>Mean latency</th><th>Cost</th></tr></thead>
            <tbody>{byVersion.map((r) => <tr key={r.v}><td>{r.v}</td><td>{r.count}</td><td>{r.mean_latency_ms} ms</td><td>{usd(r.total_cost_usd)}</td></tr>)}</tbody></table>
        </div>
      </div>
    </section>
  );
}

function Method() {
  const stats = [
    ['Population Stability Index', `Baseline decile bins, proportions floored at ${T.EPS}. Warning ${T.PSI_WARNING}, alert ${T.PSI_ALERT}: common drift-practice constants, not calibrated on real traffic.`],
    ['Mean shift in pooled SD', `Warning ${T.MEAN_SHIFT_WARNING}, alert ${T.MEAN_SHIFT_ALERT} SD (Cohen’s medium and large effects). Returns infinity when pooled SD is 0 and the means differ.`],
    ['Two-proportion z', `High alert needs a drop ≥ ${T.PASS_RATE_ALERT_DROP} and |z| ≥ ${T.Z_ALERT}; medium at drop ≥ ${T.PASS_RATE_WARNING_DROP}. Drops only: a rise in pass rate never alerts.`],
    ['Multiple comparisons', `Four metrics per window. Reported, not used for severity: KS at α ${T.KS_FAMILY_ALPHA}/3 and the pass-rate cut-off at α ${T.KS_FAMILY_ALPHA}/4 (|z| ≥ ${T.Z_BONFERRONI}).`],
  ];
  const limits = [
    'Everything is simulated: no real LLM traffic, tokens or latency. The detector separates distributions that were built to be separable.',
    `Small windows false-alarm: ${cal.false_alert[0].any_alert}/${cal.false_alert[0].runs} controls alerted at N = ${cal.false_alert[0].n} and ${cal.false_alert[1].any_alert}/${cal.false_alert[1].runs} at N = ${cal.false_alert[1].n}.`,
    'Quality is one simulated boolean. Real quality is graded, delayed and often human-judged; there is no output-text or embedding drift.',
    'Cost is derived from tokens, so alerts on both can double-count one change.',
    `Window-vs-window only. The CUSUM study shows a sequential detector catches a step in ${cal.cusum_latency.delay_records_median} records (median) but false-alarmed in ${cal.cusum_latency.false_alarm_before_change.count}/${cal.cusum_latency.runs} clean pre-change streams at h ${cal.cusum_latency.h_sd} SD.`,
    'Prices are teaching constants and Build tokens use the ceil(len/4) proxy. Runs were on a CPU VM, not the fleet node named in PROPOSAL.md.',
  ];
  return (
    <section id="method" className="card window reveal" data-title="REPORT.md — method and limits">
      <p className="eyebrow">Method and limits</p>
      <h2>What the statistics are, and <em>what they cannot</em> tell you.</h2>
      <div className="grid2" style={{ marginTop: 16 }}>
        {stats.map(([t, d]) => <div className="tile" key={t}><h3>{t}</h3><p className="hint" style={{ margin: '6px 0 0', fontSize: 13 }}>{d}</p></div>)}
      </div>
      <h3 style={{ marginTop: 24 }}>Threats to validity</h3>
      <ul className="limits">{limits.map((x) => <li key={x}>{x}</li>)}</ul>
      <div className="docs" style={{ marginTop: 12 }}>
        {[['REPORT.md', 'Report', 'Results, misses, threats and the review'], ['PROPOSAL.md', 'Proposal', 'Question, prior work, next cycle'], ['level-3-deep/calibrate.py', 'Calibration study', 'False alarms, power, CUSUM'], [`${REPO}/releases`, 'Releases', 'Tagged versions on GitHub']].map(([p, t, dsc]) => (
          <a key={p} href={p.startsWith('http') ? p : blob(p)}><b>{t}</b><small>{dsc}</small></a>
        ))}
      </div>
    </section>
  );
}
