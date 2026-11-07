"""Unit tests for the Level 3 Deep calibration study (false alerts, power, CUSUM delay)."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "level-3-deep"))
from calibrate import cusum_first_alarm, run_calibration, wilson  # noqa: E402
from run_deep import generate_window  # noqa: E402


class TestCalibration(unittest.TestCase):
    def test_generate_window_size_parameter(self):
        self.assertEqual(len(generate_window(1, 500.0, 1500.0, 0.0006, 0.92, n=37)), 37)
        # Default size and records are unchanged by the new parameter.
        self.assertEqual(generate_window(1, 500.0, 1500.0, 0.0006, 0.92)[:5],
                         generate_window(1, 500.0, 1500.0, 0.0006, 0.92, n=1000)[:5])

    def test_wilson_bounds(self):
        lo, hi = wilson(0, 50)
        self.assertEqual(lo, 0.0)
        self.assertGreater(hi, 0.0)
        lo, hi = wilson(25, 50)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)

    def test_cusum_detects_step_and_ignores_flat(self):
        flat = [0.0] * 200
        self.assertIsNone(cusum_first_alarm(flat, mu=0.0, sd=1.0))
        step = [0.0] * 100 + [2.0] * 100
        alarm = cusum_first_alarm(step, mu=0.0, sd=1.0)
        self.assertIsNotNone(alarm)
        self.assertGreaterEqual(alarm, 100)
        self.assertLess(alarm, 110)

    def test_small_run_structure_and_determinism(self):
        a = run_calibration(sizes=(100, 200), reps=4, power_n=200)
        b = run_calibration(sizes=(100, 200), reps=4, power_n=200)
        self.assertEqual(a, b)
        fa = a["false_alert"]
        self.assertEqual([row["n"] for row in fa], [100, 200])
        for row in fa:
            self.assertLessEqual(row["any_alert"], row["runs"])
            self.assertLessEqual(row["ci95"][0], row["any_alert_rate"])
        self.assertIn("latency_shift", a["power"])
        self.assertIn("pass_rate_drop", a["power"])
        self.assertIn("cusum_latency", a)


if __name__ == "__main__":
    unittest.main()
