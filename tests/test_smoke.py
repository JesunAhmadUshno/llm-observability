"""Portfolio standard layout check: required files exist and no public file carries a grade.

This repo is not pre-registered, so there is no locked proposal hash to pin.
Runs under unittest discover and as a script (python tests/test_smoke.py).
"""
import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["README.md", "PROPOSAL.md", "REPORT.md", "CHANGELOG.md", "CITATION.cff", "SECURITY.md", "LICENSE",
            "docs/decisions/0001-window-size-1000.md", "docs/decisions/0002-keep-level-folders.md",
            "level-1-learn/observability.py", "level-1-learn/run_learn.py", "level-1-learn/results_learn.json",
            "level-2-build/service.py", "level-2-build/run_build.py", "level-2-build/results_build.json",
            "level-3-deep/drift.py", "level-3-deep/run_deep.py", "level-3-deep/calibrate.py",
            "level-3-deep/results_deep.json", "level-3-deep/results_calibration.json"]
# Public grade forms: "8,700 of 10,000", "x/10000", "Grade:", "grade 8,500", rubric totals "/1000".
GRADE = re.compile(r"of 10,000|/10,?000\b|\bGrade:|\bgrade [0-9]|/1000\b", re.IGNORECASE)
README_HEADS = ["**Question.**", "**Headline.**", "**Field.**", "**Job family.**", "**Verdict.**", "## Lifecycle"]


def public_files():
    pats = ["*.md", "docs/**/*.md", "fanout/*.md", "site/src/*", "site/index.html"]
    return sorted({p for pat in pats for p in glob.glob(os.path.join(ROOT, pat), recursive=True)})


class Layout(unittest.TestCase):
    def test_required_files_exist(self):
        missing = [p for p in REQUIRED if not os.path.exists(os.path.join(ROOT, p))]
        self.assertEqual(missing, [], "missing files")

    def test_readme_opens_with_the_abstract(self):
        text = open(os.path.join(ROOT, "README.md")).read()
        pos = [text.find(h) for h in README_HEADS]
        self.assertNotIn(-1, pos, "README is missing an abstract field")
        self.assertEqual(pos, sorted(pos), "README abstract fields out of order")

    def test_no_public_grade(self):
        hits = []
        for path in public_files():
            for n, line in enumerate(open(path, encoding="utf-8"), 1):
                if GRADE.search(line):
                    hits.append(f"{os.path.relpath(path, ROOT)}:{n}: {line.strip()}")
        self.assertEqual(hits, [], "grades are internal only")

    def test_grade_pattern_catches_grades(self):
        for s in ["Grade: 8,700 of 10,000.", "grade 8,500", "Total /1000", "4/10000"]:
            self.assertTrue(GRADE.search(s), s)
        self.assertIsNone(GRADE.search("(14 / 1000) * 0.10 and graded quality"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
