# Research review: llm-observability

Reviewed 2026-11-07 against a doctoral-level research rubric. Scores are out of 5. The review covers the repo as it stands on the `site/live-dashboard` branch, including the calibration study (`level-3-deep/calibrate.py`) and the live dashboard (`site/`). Every number quoted here is in a committed results file.

**Bottom line:** a clean, deterministic, well-tested teaching build of LLM request logging, tracing and drift detection. As research it is a simulation study: it shows the detector separates distributions the author built to be separable, and now measures how often it false-alarms and how much power it has, on that same generator. It makes no claim about real LLM traffic, and should not.

| Criterion | Score | Evidence | Gap |
| --- | --- | --- | --- |
| Research question | 3 | Deep asks: can PSI, pooled-SD mean shift and a two-proportion z flag latency, cost and quality drift between windows of logged requests? | The question is about a generator, not about production LLM drift. No question about which detector is best for which drift type is stated up front. |
| Hypotheses | 2 | Implicit: control stays quiet, injected drifts alert. Met on the recorded run (control 0 alerts; latency-cost drift 3 alerts; quality drift 1 alert, pass rate 0.909 to 0.628, z -14.9). | No pre-registered hypotheses or effect sizes of interest. Thresholds were fixed before the run, which helps. |
| Method | 3 | Baseline-quantile PSI with EPS smoothing, mean shift in pooled SD, two-proportion z, severity rules with stated reasons (`level-3-deep/drift.py`). | Thresholds are literature constants (PSI 0.10/0.25, 0.5/1.0 SD, drop 0.05/0.10 with z 1.96), not learned. The pass-rate check is one-sided (drops only), now documented. |
| Baselines | 3 | Fixed now: two-sample KS per numeric metric and a one-sided CUSUM on a latency stream, in `calibrate.py`. KS is clearly more powerful for small latency shifts (see Deep README table). | No comparison with an existing observability tool (Langfuse class). `NOVELTY.md` still says NO MEASUREMENT YET. |
| Statistics and uncertainty | 3 | Fixed now: false-alert rate and detection power over 50 seed pairs per setting with Wilson 95% intervals; Bonferroni z field (alpha/4) and KS at alpha/3. | 50 runs give wide intervals (0/50 still allows up to 7%). Cost and tokens are correlated by construction, so the four tests are not independent. |
| Reproducibility | 5 | Seeded stdlib generators; CI runs every level's tests and runners and fails if any committed result changes (one named timing field excepted). Verified locally on 2026-11-07: `run_deep.py` and `calibrate.py` reproduce their JSON byte for byte. The site's build re-runs the detector in JavaScript (exact MT19937 port) and fails if it does not match `results_deep.json` and the false-alert counts. | None at this scale. |
| Threats to validity | 3 | Level READMEs list failure modes: simulated only, small windows, bin-edge sensitivity, boolean quality, cost/token double counting, no alert delivery. | External validity is the main threat and is not addressable without real traffic. |
| Related work | 1 | PSI, KS and CUSUM (Page, 1954) are standard; Wilson (1927) intervals. | `DOSSIER.md` defers prior art; there is no dated literature review of LLM observability or drift detection. |
| Limitations stated | 4 | Every level states simulated traffic, teaching price constants, the ceil(len/4) token proxy, and self-deducts for each (grades 8,700 / 8,700 / 8,500). | Runs were on the Muse VM, not the fleet node in SPEC (deducted in the READMEs). |
| Engineering rigor | 4 | 58 tests (`python3 -m pytest -q`), ruff lint, 3.11 and 3.12 matrix, deterministic artifacts, stdlib only. | Learn's 10 requests sit on a clean 100 to 1000 ms ladder, so percentiles there are trivial. |

## Fixed on this branch (cheap, CPU, seconds)

1. Dead branch in `two_proportion_z` (`z = 0.0 if p1 == p2 else 0.0`) removed, with zero-SE tests.
2. KS baseline and Bonferroni fields added to `detect_drift` output; `results_deep.json` alert outcomes unchanged.
3. Calibration study (`calibrate.py`, `results_calibration.json`): false alerts on the control are 50/50 at N = 100 and 38/50 at N = 200, then 0/50 from N = 500. This quantifies the README's old note that PSI fired on the control at 200 records.
4. CI now runs the Deep tests, `run_deep.py` and `calibrate.py`, and checks the committed results reproduce.
5. `docs/index.md` no longer says "Deep: not started".
6. Deep README states the one-sided pass-rate check and carries the calibration tables.
7. The dashboard re-runs the detector live, with build-time parity checks (`site/src/drift.check.mjs`, `site/src/obs.check.mjs`).

## Remaining gaps and exactly what each needs

| Gap | What it needs |
| --- | --- |
| No real traffic: every request, token, latency and quality value is simulated. | A log of real LLM calls: at least two windows of 1,000+ requests each from one service, with timestamps, model, prompt version, measured latency, provider-reported tokens and cost. Either a small paid API budget, or a local model server (CPU or one GPU) driven by a fixed prompt set. |
| Thresholds not calibrated on real data. | The same real log, split into many no-drift window pairs, to set PSI and SD thresholds for a target false-alert rate (for example 1% per window). |
| Quality is one simulated boolean. | Graded quality labels on real outputs: a labelled eval set (a few hundred prompts with reference answers or a rubric) and either human grading or a scored judge, plus the delay between output and label. |
| No output-text or embedding drift. | Real output text and an embedding model (CPU is enough for a small sentence encoder over a few thousand outputs). |
| No comparison with an existing tool. | A self-hosted Langfuse-class stack ingesting the same real log, with the same injected changes, to compare alerts and detection delay. |
| Tight intervals. | More repetitions (for example 500 per setting instead of 50): CPU only, roughly 10 times the current 4 s run, so cheap whenever needed. |
| Sequential detection delay only for latency. | Extend the CUSUM stream to tokens, cost and pass rate (CPU, seconds); with real data, measure delay on a timestamped incident. |
| No literature review. | A dated review of drift-detection and LLM-observability sources, written into `DOSSIER.md` with links. Reading time only. |
