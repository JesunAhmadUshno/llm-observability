"""Unit tests for Level 1 Learn observability. Hand-computed values."""
import hashlib
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "level-1-learn"))
from observability import (  # noqa: E402
    ManualClock,
    ObservabilityError,
    RequestLogger,
    Tracer,
    VersionRegistry,
    aggregate,
    compute_cost,
    percentile,
    prompt_hash,
)


class TestCost(unittest.TestCase):
    def test_cost_small(self):
        # (1000/1000)*0.10 + (500/1000)*0.20 = 0.10 + 0.10 = 0.20
        self.assertEqual(compute_cost("alpha-small", 1000, 500), 0.20)

    def test_cost_large(self):
        # (2000/1000)*0.50 + (1000/1000)*1.00 = 1.00 + 1.00 = 2.00
        self.assertEqual(compute_cost("alpha-large", 2000, 1000), 2.00)

    def test_cost_zero_tokens(self):
        self.assertEqual(compute_cost("alpha-small", 0, 0), 0.0)

    def test_cost_unknown_model(self):
        with self.assertRaises(ObservabilityError):
            compute_cost("no-such-model", 10, 10)

    def test_cost_negative_tokens(self):
        with self.assertRaises(ObservabilityError):
            compute_cost("alpha-small", -1, 10)


class TestLogger(unittest.TestCase):
    def test_record_fields_and_hash(self):
        log = RequestLogger()
        r = log.log_request("R01", "hello world", "alpha-small",
                            1000, 500, 100, "v1", "v1")
        self.assertEqual(r["total_tokens"], 1500)
        self.assertEqual(r["cost_usd"], 0.20)
        self.assertEqual(r["prompt_hash"],
                         hashlib.sha256(b"hello world").hexdigest())
        self.assertEqual(prompt_hash("hello world"), r["prompt_hash"])
        self.assertEqual(r["prompt_version"], "v1")

    def test_json_lines_parse(self):
        log = RequestLogger()
        log.log_request("R01", "a", "alpha-small", 500, 250, 200)
        log.log_request("R02", "b", "alpha-large", 2000, 1000, 300)
        lines = log.to_json_lines().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[1])["cost_usd"], 2.00)

    def test_negative_latency_rejected(self):
        log = RequestLogger()
        with self.assertRaises(ObservabilityError):
            log.log_request("R01", "a", "alpha-small", 1, 1, -5)


class TestPercentileAndAggregate(unittest.TestCase):
    def test_percentile_nearest_rank(self):
        values = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
        # p50: ceil(0.50*10)=5th value = 500. p95: ceil(9.5)=10th = 1000.
        self.assertEqual(percentile(values, 50), 500)
        self.assertEqual(percentile(values, 95), 1000)
        self.assertEqual(percentile(values, 0), 100)

    def test_percentile_empty_rejected(self):
        with self.assertRaises(ObservabilityError):
            percentile([], 50)

    def _records(self):
        log = RequestLogger()
        log.log_request("R01", "x", "alpha-small", 1000, 500, 100)
        log.log_request("R02", "y", "alpha-large", 2000, 1000, 300)
        return log.records

    def test_aggregate_totals(self):
        s = aggregate(self._records())
        self.assertEqual(s["count"], 2)
        self.assertEqual(s["prompt_tokens"], 3000)
        self.assertEqual(s["completion_tokens"], 1500)
        self.assertEqual(s["total_tokens"], 4500)
        # 0.20 + 2.00 = 2.20
        self.assertEqual(s["total_cost_usd"], 2.20)
        self.assertEqual(s["mean_latency_ms"], 200.0)

    def test_aggregate_per_model(self):
        s = aggregate(self._records())
        self.assertEqual(s["per_model"]["alpha-small"]["count"], 1)
        self.assertEqual(s["per_model"]["alpha-small"]["total_cost_usd"],
                         0.20)
        self.assertEqual(s["per_model"]["alpha-large"]["total_tokens"],
                         3000)

    def test_aggregate_empty(self):
        s = aggregate([])
        self.assertEqual(s["count"], 0)
        self.assertEqual(s["per_model"], {})


class TestTracer(unittest.TestCase):
    def test_span_nesting_and_duration(self):
        clock = ManualClock()
        tracer = Tracer(clock.now)
        with tracer.span("root"):
            clock.advance(50)
            with tracer.span("child"):
                clock.advance(30)
        spans = {s["name"]: s for s in tracer.spans()}
        self.assertEqual(spans["root"]["duration_ms"], 80)
        self.assertEqual(spans["child"]["duration_ms"], 30)
        self.assertEqual(spans["child"]["parent_id"],
                         spans["root"]["span_id"])
        self.assertEqual(spans["root"]["children"],
                         [spans["child"]["span_id"]])
        self.assertEqual(len(tracer.roots()), 1)

    def test_span_ids_deterministic(self):
        clock = ManualClock()
        tracer = Tracer(clock.now)
        with tracer.span("a"):
            pass
        with tracer.span("b"):
            pass
        self.assertEqual([s["span_id"] for s in tracer.spans()],
                         ["span-1", "span-2"])
        self.assertEqual(len(tracer.roots()), 2)

    def test_clock_cannot_go_backwards(self):
        clock = ManualClock()
        with self.assertRaises(ObservabilityError):
            clock.advance(-1)


class TestRegistry(unittest.TestCase):
    def test_register_and_resolve_latest(self):
        reg = VersionRegistry()
        reg.register("prompt", "p", "v1", "one")
        reg.register("prompt", "p", "v2", "two")
        self.assertEqual(reg.resolve("prompt", "p")["content"], "two")
        self.assertEqual(reg.list_versions("prompt", "p"), ["v1", "v2"])

    def test_resolve_specific_version(self):
        reg = VersionRegistry()
        reg.register("model", "m", "v1", "first")
        reg.register("model", "m", "v2", "second")
        self.assertEqual(reg.resolve("model", "m", "v1")["content"],
                         "first")

    def test_duplicate_version_rejected(self):
        reg = VersionRegistry()
        reg.register("prompt", "p", "v1", "one")
        with self.assertRaises(ObservabilityError):
            reg.register("prompt", "p", "v1", "again")

    def test_unknown_name_and_kind_rejected(self):
        reg = VersionRegistry()
        with self.assertRaises(ObservabilityError):
            reg.resolve("prompt", "missing")
        with self.assertRaises(ObservabilityError):
            reg.register("dataset", "p", "v1", "x")

    def test_changelog_order(self):
        reg = VersionRegistry()
        reg.register("prompt", "p", "v1", "one")
        reg.register("model", "m", "v1", "model one")
        self.assertEqual(reg.changelog(),
                         [{"kind": "prompt", "name": "p", "version": "v1"},
                          {"kind": "model", "name": "m", "version": "v1"}])


if __name__ == "__main__":
    unittest.main()
