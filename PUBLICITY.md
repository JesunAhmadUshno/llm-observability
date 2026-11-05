# PUBLICITY: llm-observability (P12)

Publicity log under the documentation and publishing standard,
Section 7. Every finished level produces its written fan-out set,
each piece graded on the 1,000-point publicity rubric (accuracy 300,
research 200, gap fit 200, clarity 150, reach format 150), ship line
900. Drafts are prepared by the loop. Actual social posting follows
the standing platform rules and gates. The loop itself never posts
to social.

Project state on 2026-11-05: Learn DONE and Build DONE, both graded
8,700 of 10,000, 39 tests passing. Deep is not started. All requests
in both levels are simulated and labelled as simulated; no real LLM
was called.

## Actions polish pack (2026-11-05)

Applied through a pull request on 2026-11-05, following the Actions
polish pack standard. The pack adds: CI on a Python 3.11 and 3.12
matrix with a ruff lint step (all pre-existing P12 CI steps
preserved: smoke test, Learn tests and Learn runner, and the Build
tests and Build runner added alongside them), CodeQL scanning,
Dependabot for pip and GitHub Actions, a release workflow that
attaches a source tarball named llm-observability-<tag>.tar.gz to
v* tag releases, Labeler, Greetings (snake_case inputs for
actions/first-interaction@v3: repo_token, issue_message,
pr_message), Stale in comment-only mode (days-before-close: -1,
never closes), and a docs summary page at docs/index.md for
GitHub Pages. Ruff scope is recorded in ruff.toml (E, F, I,
line-length 120). Ruff fixes in this pull request were style
only: 4 initial errors (3 import order, 1 long line), fixed by
ruff fix output and a noqa E501 marker on the pre-existing
benchmark_label string line, whose string value is unchanged,
with no change to behaviour. requirements.txt records the
standard-library-only fact so Dependabot pip has a manifest to
watch.

| Channel | Outcome on 2026-11-05 |
| --- | --- |
| GitHub Pages | Docs page added at docs/index.md in this pull request. Pages enablement and live build status are verified after merge and recorded in the batch ledger; no live claim is made in this file before that check. |
| Release workflow | Held: unproven until the next v* tag creates a release with the tarball attached. No tag was created in this cycle. |
| PyPI publishing | Held: needs a PyPI token, a new credential. Jesun's tap only. Not set up. |
| Social channels (LinkedIn, X, Facebook, Instagram, Threads) | Held: no posts made. The loop never posts to social; Threads waits for Jesun's tap per post under the standing gates. |

Publicity grade for this polish pack log piece, on the 1,000
point rubric (accuracy 300, research 200, gap fit 200, clarity
150, reach format 150), ship line 900:

| Piece | Accuracy /300 | Research /200 | Gap fit /200 | Clarity /150 | Reach /150 | Total /1000 |
| --- | --- | --- | --- | --- | --- | --- |
| PUBLICITY.md polish pack section (2026-11-05) | 295 | 180 | 195 | 145 | 100 | 915 |

At or above the 900 ship line. Named deductions: research minus
20, because the pack is a standard applied across repos and this
section records its application rather than new research; reach
minus 50, because the docs page is copy in this pull request with
no live Pages claim yet, the release workflow is unproven until
the next tag, PyPI publishing is held, and no social channel
carries this piece by the standing gates; accuracy minus 5, gap
fit minus 5, and clarity minus 5 for summary compression of the
full pack standard, which lives in the batch files.
