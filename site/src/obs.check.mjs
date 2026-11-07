// Known-answer check, run by npm run build: cost, percentile, store parsing, registry diff and
// grade parsing must reproduce the numbers in results_learn.json, results_build.json and the READMEs.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { parsePriceTable, computeCost, percentile, summarize, parseStore, parsePrompts, diffLines, parseGrade, countTests } from './obs.js';

const read = (p) => fs.readFileSync(new URL(`../../${p}`, import.meta.url), 'utf8');
const learn = JSON.parse(read('level-1-learn/results_learn.json'));
const build = JSON.parse(read('level-2-build/results_build.json'));
const table = parsePriceTable(read('level-1-learn/observability.py'));
assert.deepEqual(Object.keys(table).sort(), ['alpha-large', 'alpha-small']);

const store = parseStore(read('level-2-build/store_build.jsonl'));
assert.equal(store.length, build.summary.count);
assert.equal(store.reduce((n, r) => n + r.spans.length, 0), build.span_count);
assert.deepEqual(store.map((r) => r.request_id), build.records.map((r) => r.request_id));

let costs = 0;
for (const r of [...learn.records, ...build.records, ...store]) {
  assert.equal(computeCost(table, r.model, r.prompt_tokens, r.completion_tokens), r.cost_usd, `cost ${r.request_id}`);
  costs++;
}
for (const [name, res, recs] of [['learn', learn, learn.records], ['build', build, store]]) {
  const s = summarize(recs);
  for (const k of Object.keys(s)) assert.equal(s[k], res.summary[k], `${name} summary ${k}`);
  for (const [m, want] of Object.entries(res.summary.per_model)) {
    const got = summarize(recs.filter((r) => r.model === m));
    for (const k of Object.keys(got)) assert.equal(got[k], want[k], `${name} ${m} ${k}`);
  }
  assert.equal(percentile(recs.map((r) => r.latency_ms), 50), res.summary.p50_latency_ms);
  assert.equal(percentile(recs.map((r) => r.latency_ms), 95), res.summary.p95_latency_ms);
}
// Each persisted trace: root span covers the request latency, children sum to it.
for (const r of store) {
  const root = r.spans.find((s) => s.parent_id === null);
  assert.equal(root.duration_ms, r.latency_ms, `root span ${r.request_id}`);
  assert.equal(r.spans.filter((s) => s.parent_id === root.span_id).reduce((a, s) => a + s.duration_ms, 0), r.latency_ms);
}

const prompts = parsePrompts(read('level-2-build/run_build.py'));
const want = build.registry_diff_prompt_v1_v2;
const d = diffLines(prompts[want.old_version].lines, prompts[want.new_version].lines);
assert.deepEqual(d.added, want.diff.added);
assert.deepEqual(d.removed, want.diff.removed);
assert.equal(d.unchanged, want.diff.unchanged);

const grades = ['level-1-learn', 'level-2-build', 'level-3-deep'].map((l) => parseGrade(read(`${l}/README.md`)));
for (const g of grades) assert.equal(g.grade + g.deductions.reduce((a, x) => a + x.points, 0), g.of, `deductions sum for grade ${g.grade}`);

const tests = countTests(fs.readdirSync(new URL('../../tests/', import.meta.url)).filter((f) => f.endsWith('.py')).map((f) => read(`tests/${f}`)));
assert.ok(tests >= 47, `test count ${tests}`);
console.log('obs ok', { costsChecked: costs, grades: grades.map((g) => g.grade), tests });
