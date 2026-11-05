# PUBLICITY: llm-observability (P12)

Publicity log under the documentation and publishing standard,
Section 7. Every finished level produces its written fan-out set,
each piece graded on the 1,000-point publicity rubric (accuracy 300,
research 200, gap fit 200, clarity 150, reach format 150), ship line
900. Drafts are prepared by the loop. Actual social posting follows
the standing platform rules and gates. The loop itself never posts
to social.

Fan-out set date: 2026-11-05. Project state: v1.0, Learn, Build,
and compressed Deep done 2026-11-05, 47 tests passing. Level
grades on record: Learn 8,700 of 10,000, Build 8,700 of 10,000,
Deep 8,500 of 10,000. Deep detail: a drift detector (PSI, mean
shift, two-proportion z on a simulated quality field) over windows
of 1,000 records each; control 0 alerts severity none with latency
PSI 0.025905; latency and cost drift 3 alerts severity high with
latency PSI 8.045714 and mean shift 4.480065; quality drift 1
alert severity high with the simulated pass rate falling from
0.909 to 0.628, a drop of 0.281. All data is simulated and labelled
as simulated; no real LLM was called, and quality is a simulated
logged field, never real model quality.

## Channel log (2026-11-05)

| Channel | Outcome on 2026-11-05 |
| --- | --- |
| GitHub releases | Live: v0.1 https://github.com/JesunAhmadUshno/llm-observability/releases/tag/v0.1 , v0.5 https://github.com/JesunAhmadUshno/llm-observability/releases/tag/v0.5 , v1.0 https://github.com/JesunAhmadUshno/llm-observability/releases/tag/v1.0 (verified with gh release list, 2026-11-05). Draft release notes for all three are in fanout/release-notes.md. No new release was created for the fan-out. |
| Portfolio index | Held: fan-out links are ready, the index update is a coordinator step outside this cycle. Named reason: held for index refresh. |
| Website page | Draft in fanout/website-page.md. Held: not published to jesunahmadushno.com. |
| Blog | Draft in fanout/blog-post.md. Held: not posted. |
| Tutorial | In repo: fanout/tutorial.md. Every command in it was run and verified on 2026-11-05 (three runners, three per-level test modules, scaffold smoke test, full suite at 47 tests). |
| LinkedIn post | Draft in fanout/linkedin-post.md, marked DRAFT NOT POSTED, link carried as the first-comment line per the LinkedIn rule. Held: not posted, loop never posts. |
| X | Draft held: no X copy is shipped in this set beyond the LinkedIn draft source text. Held under the standing social rules; posting is outside the loop. |
| Facebook | Draft held: no Facebook copy posted. Standing rule applies (no link in body or comments, keyword call to action fulfilled by DM). Held: not posted, loop never posts. |
| Instagram | Draft held: no Instagram copy posted. Standing rule applies (no clickable link in caption, link in bio). Held: not posted, loop never posts. |
| Threads | Draft held: no Threads copy posted. Threads waits for Jesun's tap per post, hash-locked on exact text and media. Held: awaiting Jesun's tap. |
| Video | Held: engine queue, January production for lab projects per the December Compression Protocol. No video was produced in this cycle. |
| Book chapter | Draft angle in fanout/blog-post.md and SPEC.md ("Watching The Machine Think"). Held: chapter draft follows the finished project set; not a published chapter. |
| Paper candidate | Draft brief in fanout/paper-candidate.md (drift detection note, seeded-drift form). Submission is Jesun's tap. Nothing submitted, no venue contacted. The publications tracker is updated by the coordinator, not by this cycle. |

## Publicity grades (1,000-point rubric, ship line 900)

| Piece | Accuracy /300 | Research /200 | Gap fit /200 | Clarity /150 | Reach format /150 | Total /1000 |
| --- | --- | --- | --- | --- | --- | --- |
| fanout/blog-post.md | 295 | 188 | 194 | 145 | 140 | 962 |
| fanout/tutorial.md | 298 | 185 | 195 | 148 | 142 | 968 |
| fanout/website-page.md | 293 | 180 | 190 | 147 | 145 | 955 |
| fanout/linkedin-post.md | 288 | 175 | 190 | 145 | 140 | 938 |
| fanout/paper-candidate.md | 293 | 195 | 194 | 140 | 130 | 952 |
| fanout/release-notes.md | 296 | 183 | 184 | 144 | 138 | 945 |

All six pieces are at or above the 900 ship line. No piece was
shipped ungraded. Overall fan-out grade: 9,533 of 10,000 (mean of
the six piece totals, 953 of 1,000).

## Named deductions (unclosable in this cycle)

- Blog post, minus 38: research is condensed from DOSSIER.md v1,
  whose prior art section is brief (minus 12 research); simulated
  data limits how far the results travel, stated in the piece
  (minus 10 reach, minus 5 accuracy for reader interpretation
  risk, minus 6 gap fit, minus 5 clarity).
- Tutorial, minus 32: research framing is thinner than the blog by
  design, because the module teaches runs rather than the field
  (minus 15 research); no worked example beyond the shipped sets
  (minus 5 gap fit, minus 2 clarity, minus 8 reach, minus 2
  accuracy).
- Website page, minus 45: condensed research (minus 20), condensed
  gap framing (minus 10), and the page is copy only, not a live
  page (minus 5 reach, minus 7 accuracy, minus 3 clarity).
- LinkedIn post, minus 62: short form compresses the research and
  the failure mode detail (minus 25 research, minus 12 accuracy,
  minus 10 gap fit, minus 5 clarity, minus 10 reach, because the
  post is a held draft and carries no live link in the body by rule).
- Paper candidate, minus 48: this is a brief, not a drafted paper
  (minus 20 reach, minus 10 clarity); venue is classed, not named
  (minus 5 research, minus 6 gap fit, minus 7 accuracy for the
  simulated-only evidence base the paper must carry).
- Release notes, minus 55: notes summarise releases that already
  exist, so research and gap framing are summary grade (minus 17
  research, minus 16 gap fit); format is repo-bound (minus 12
  reach, minus 4 accuracy, minus 6 clarity).

## Jev gate (2026-11-05)

claim_check on the blog main results paragraph, extracted
byte-exact from fanout/blog-post.md by script. Spec:
hidden_files/jev-p12-fanout-claim-spec-2026-11-05.json in the goal
workspace. Results:
hidden_files/jev-p12-fanout-claim-results-2026-11-05.json. Model
jev-1.13.0, question id supported, noul 0.78, route REVIEW (clear
at 0.85 or above, block at 0.10 or below, review between), input
tokens 1468, output tokens 20. Arithmetic was pre-computed in the
spec evidence (15,500 plus 7,250 is 22,750; 876 plus 1,332 is
2,208; 21 plus 18 is 39 and 39 plus 8 is 47; 0.909 minus 0.628 is
0.281). No claim was blocked.

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
