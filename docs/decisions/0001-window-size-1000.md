# 0001: Drift windows of 1,000 records

Date: 2026-11-05. Status: accepted.

Context. The first Deep run used 200 records per window. PSI sampling
noise fired medium alerts on the no-drift control.

Decision. Raise every window to 1,000 records and record the change and
its reason (REPORT.md, Drift detection). This was decided after seeing a
result, which is one reason the repo is not pre-registered.

Consequences. The calibration study (2026-11-07) later measured the
effect: 50/50 false alerts at N = 100, 38/50 at N = 200, 0/50 from
N = 500 up. A locked confirmatory cycle must fix the window size before
any run.
