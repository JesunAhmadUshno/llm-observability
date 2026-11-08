# Changelog

All notable changes to this project. Format: Keep a Changelog 1.1.
Versions follow Semantic Versioning. The tags v0.1, v0.5 and v1.0 were
cut under the old Learn / Build / Deep ladder; under the portfolio
standard v2 the repo's verdict is Functional, not "v1.0 Released".

## [Unreleased]

### Changed
- 2026-11-08: Independent review applied. One-command reproduce,
  scripts/reproduce.sh, documented in the README and run in CI. The
  results_build.json benchmark_label no longer claims the Muse VM for a
  timing every machine re-measures. CITATION.cff drops date-released
  (the old v1.0 tag date) until a release under standard v2. Grades
  removed from the v0.1, v0.5 and v1.0 GitHub release notes; tags
  unchanged.
- 2026-11-08: Restructured to the portfolio standard v2. README is the
  abstract (question, headline with its interval, field, job family,
  verdict: Functional, not pre-registered). PROPOSAL.md gathers SPEC.md,
  LEARN-SPEC.md, NOVELTY.md, DOSSIER.md and ROADMAP.md. REPORT.md gathers
  the three level READMEs and docs/research-review.md, and scores the
  three after-the-fact hypotheses with their misses. PUBLICITY.md moved
  to fanout/. Scores and grades left the public files. Code stays in the
  level-*/ folders (decision 0002). The dashboard no longer shows grades
  and links PROPOSAL.md and REPORT.md.
- 2026-11-08: CI declares read-only permissions and runs the layout
  check; CodeQL also scans the dashboard's JavaScript; Dependabot
  watches site/ npm packages.

### Added
- 2026-11-08: tests/test_smoke.py checks the required files and that no
  public file carries a grade. CHANGELOG.md, CITATION.cff, SECURITY.md,
  docs/decisions/ 0001 and 0002.
- 2026-11-07: Live dashboard on GitHub Pages (site/), with JavaScript
  ports of the detector held to the Python results by build-time checks.
- 2026-11-07: Research review (now in REPORT.md).
- 2026-11-07: Calibration study (calibrate.py): false alerts by window
  size, detection power against KS and Bonferroni baselines, CUSUM
  delay, 50 seed pairs per setting with Wilson intervals. CI regenerates
  every result file and fails on any change.

### Fixed
- 2026-11-07: Dead zero-SE branch in two_proportion_z removed, with tests.

## [1.0] - 2026-11-05
### Added
- Drift detection and alerts (level-3-deep): PSI, pooled-SD mean shift,
  two-proportion z over seeded simulated windows of 1,000 records.

## [0.5] - 2026-11-05
### Added
- Persistent JSONL store, service with nested spans, registry diff,
  static dashboard over 60 simulated requests (level-2-build).
- Actions pack: CI matrix, ruff, CodeQL, Dependabot, release workflow.

## [0.1] - 2026-11-05
### Added
- Request logger, tracer and version registry on 10 labelled simulated
  requests (level-1-learn).
