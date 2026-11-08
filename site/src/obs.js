// Ports of level-1-learn/observability.py (compute_cost, percentile, _summarize) and
// parsers for the repo files the page reads at build time. obs.check.mjs proves parity.
import { pyRound } from './drift.js';

// PRICE_TABLE is parsed from observability.py so the page shows exactly the stated teaching constants.
export function parsePriceTable(src) {
  const block = src.match(/PRICE_TABLE = \{([\s\S]*?)\n\}/);
  if (!block) throw new Error('PRICE_TABLE not found in observability.py');
  const table = {};
  for (const m of block[1].matchAll(/"([\w-]+)":\s*\{"input_per_1k":\s*([\d.]+),\s*"output_per_1k":\s*([\d.]+)\}/g))
    table[m[1]] = { input_per_1k: Number(m[2]), output_per_1k: Number(m[3]) };
  if (!Object.keys(table).length) throw new Error('PRICE_TABLE parsed empty');
  return table;
}

export function computeCost(table, model, promptTokens, completionTokens) {
  const r = table[model];
  if (!r) throw new Error(`unknown model: ${model}`);
  return pyRound((promptTokens / 1000) * r.input_per_1k + (completionTokens / 1000) * r.output_per_1k, 6);
}

// Nearest rank: rank = ceil(p / 100 * n), 1-indexed into the sorted values.
export function percentile(values, p) {
  const s = [...values].sort((a, b) => a - b);
  const rank = Math.max(1, Math.min(Math.ceil((p / 100) * s.length), s.length));
  return s[rank - 1];
}

const sum = (xs) => xs.reduce((a, b) => a + b, 0);
export function summarize(records) {
  const lat = records.map((r) => r.latency_ms);
  return {
    count: records.length,
    total_tokens: sum(records.map((r) => r.total_tokens)),
    total_cost_usd: pyRound(sum(records.map((r) => r.cost_usd)), 6),
    mean_latency_ms: lat.length ? pyRound(sum(lat) / lat.length, 3) : 0,
    p50_latency_ms: lat.length ? percentile(lat, 50) : 0,
    p95_latency_ms: lat.length ? percentile(lat, 95) : 0,
  };
}

// store_build.jsonl: each record line is followed by the spans of its trace.
export function parseStore(text) {
  const out = [];
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    const { type, data } = JSON.parse(line);
    if (type === 'record') out.push({ ...data, spans: [] });
    else if (type === 'span' && out.length) out[out.length - 1].spans.push(data);
  }
  return out;
}

// Prompt versions are read from the register() calls in run_build.py.
export function parsePrompts(src) {
  const versions = {};
  for (const m of src.matchAll(/register\("prompt", "([\w-]+)", "(v\d+)",\s*"([^"]*)"\)/g))
    versions[m[2]] = { name: m[1], lines: m[3].split('\\n') };
  return versions;
}

export function diffLines(oldLines, newLines) {
  const o = new Set(oldLines), n = new Set(newLines);
  return {
    added: newLines.filter((l) => !o.has(l)),
    removed: oldLines.filter((l) => !n.has(l)),
    unchanged: oldLines.filter((l) => n.has(l)).length,
  };
}

export const countTests = (sources) => sources.reduce((n, s) => n + (s.match(/^\s*def test_/gm) || []).length, 0);
