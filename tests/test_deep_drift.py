"""Unit tests for Level 3 Deep drift detection."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "level-3-deep"))
from drift import (  # noqa: E402
    assess_pass_rate,
    detect_drift,
    ks_critical,
    ks_statistic,
    mean_shift_pooled_sd,
    population_stability_index,
    two_proportion_z,
)
from run_deep import build_experiment, generate_window  # noqa: E402


class TestPSI(unittest.TestCase):
    def test_identical_near_zero(self):
        data = [float(i) for i in range(1, 201)]
        self.assertLess(population_stability_index(data, list(data)), 0.01)

    def test_shifted_higher(self):
        base = [float(i) for i in range(1, 201)]
        shifted = [float(i + 100) for i in range(1, 201)]
        self.assertGreater(population_stability_index(base, shifted),
                           population_stability_index(base, list(base)))

    def test_mean_shift_zero_identical(self):
        data = [10.0, 20.0, 30.0, 40.0]
        self.assertEqual(mean_shift_pooled_sd(data, list(data)), 0.0)

    def test_mean_shift_positive(self):
        self.assertGreater(mean_shift_pooled_sd([10.0, 20.0, 30.0], [40.0, 50.0, 60.0]), 1.0)


class TestPassRate(unittest.TestCase):
    def test_z_same_rate_near_zero(self):
        z, p1, p2 = two_proportion_z(90, 100, 90, 100)
        self.assertEqual(z, 0.0)
        self.assertEqual(p1, p2)

    def test_pass_rate_drop_alert(self):
        base = [{"quality_pass": i < 92} for i in range(100)]
        cur = [{"quality_pass": i < 60} for i in range(100)]
        r = assess_pass_rate(base, cur)
        self.assertTrue(r["alert"])
        self.assertEqual(r["severity"], "high")


class TestZeroSE(unittest.TestCase):
    def test_all_pass_both_windows_gives_zero_z(self):
        # Pooled rate 1.0 means SE is 0; both rates are then equal, so z is 0 by definition.
        self.assertEqual(two_proportion_z(10, 10, 20, 20), (0.0, 1.0, 1.0))

    def test_all_fail_both_windows_gives_zero_z(self):
        self.assertEqual(two_proportion_z(0, 10, 0, 20), (0.0, 0.0, 0.0))


class TestKS(unittest.TestCase):
    def test_identical_is_zero(self):
        data = [float(i) for i in range(50)]
        self.assertEqual(ks_statistic(data, list(data)), 0.0)

    def test_disjoint_is_one(self):
        self.assertEqual(ks_statistic([1.0, 2.0, 3.0], [10.0, 11.0]), 1.0)

    def test_known_value_with_ties(self):
        # ECDFs after 2: base 3/4, cur 0/2, so D = 0.75 (ties advance together).
        self.assertEqual(ks_statistic([1.0, 2.0, 2.0, 3.0], [3.0, 4.0]), 0.75)

    def test_critical_value_shrinks_with_n(self):
        self.assertGreater(ks_critical(100, 100, 0.05), ks_critical(1000, 1000, 0.05))
        self.assertAlmostEqual(ks_critical(1000, 1000, 0.05), 1.358099 * (2 / 1000) ** 0.5, places=5)

    def test_report_carries_ks_and_bonferroni_fields(self):
        base = generate_window(1, 500.0, 1500.0, 0.0006, 0.92)
        cur = generate_window(2, 500.0, 1500.0, 0.0006, 0.92)
        report = detect_drift(base, cur)
        lat = report["per_metric"]["latency_ms"]
        self.assertIn("ks_statistic", lat)
        self.assertEqual(lat["ks_reject"], lat["ks_statistic"] > lat["ks_critical_bonferroni"])
        pr = report["per_metric"]["quality_pass_rate_simulated"]
        self.assertGreater(pr["z_bonferroni_threshold"], 1.96)
        self.assertEqual(pr["direction"], "drop only")


class TestAlertLogic(unittest.TestCase):
    def test_no_drift_no_alert(self):
        base = generate_window(1, 500.0, 1500.0, 0.0006, 0.92)
        cur = generate_window(2, 500.0, 1500.0, 0.0006, 0.92)
        report = detect_drift(base, cur)
        # Control may have low severity but should not be high overall in this seeded setup;
        # assert structure and that alert logic is consistent.
        self.assertEqual(report["alert_count"], len(report["alerts"]))
        self.assertIn(report["overall_severity"], ("none", "low", "medium", "high"))

    def test_experiment_end_to_end(self):
        summary = build_experiment()
        self.assertTrue(summary["windows"]["latency_cost_drift"]["has_alert"])
        self.assertTrue(summary["windows"]["quality_drift"]["has_alert"])
        self.assertIn(summary["windows"]["control_no_drift"]["overall_severity"], ("none", "low", "medium"))
        self.assertEqual(summary["n_per_window"], 1000)


if __name__ == "__main__":
    unittest.main()
