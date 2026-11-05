"""Unit tests for Level 2 Build service. Hand-computed values where stated."""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "level-1-learn"))
sys.path.insert(0, os.path.join(ROOT, "level-2-build"))

from observability import ManualClock, VersionRegistry, aggregate  # noqa: E402
from service import (  # noqa: E402
    LogStore,
    ObservabilityService,
    diff_entries,
    diff_text,
    generate_dashboard,
    proxy_token_count,
    registry_diff,
)


class TestProxy(unittest.TestCase):
    def test_proxy_counts(self):
        self.assertEqual(proxy_token_count(""), 0)
        self.assertEqual(proxy_token_count("a"), 1)
        self.assertEqual(proxy_token_count("abcd"), 1)
        self.assertEqual(proxy_token_count("abcde"), 2)
        self.assertEqual(proxy_token_count("hello world"), 3)  # ceil(11/4)=3

    def test_proxy_is_deterministic(self):
        self.assertEqual(proxy_token_count("same text"),
                         proxy_token_count("same text"))


class TestLogStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "store.jsonl")

    def tearDown(self):
        self.tmp.cleanup()

    def test_persistence_round_trip_records_and_spans(self):
        store = LogStore(self.path)
        store.append_record({"request_id": "R1", "total_tokens": 10})
        store.append_span({"span_id": "span-1", "name": "root"})
        store.append_spans([{"span_id": "span-2", "name": "child"}])
        records, spans, corrupt = store.load_all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["request_id"], "R1")
        self.assertEqual(len(spans), 2)
        self.assertEqual(corrupt, 0)

    def test_load_missing_file_returns_empty(self):
        store = LogStore(self.path)
        self.assertEqual(store.load_records(), [])
        self.assertEqual(store.load_spans(), [])

    def test_corrupt_line_handling(self):
        store = LogStore(self.path)
        store.append_record({"request_id": "R1"})
        with open(self.path, "a", encoding="utf-8") as f:
            f.write("this is not json\n")
            f.write('{"no_type": true}\n')
        store.append_record({"request_id": "R2"})
        records, spans, corrupt = store.load_all()
        self.assertEqual([r["request_id"] for r in records], ["R1", "R2"])
        self.assertEqual(corrupt, 2)
        self.assertEqual(store.last_corrupt_count, 2)

    def test_reload_matches_appended_order(self):
        store = LogStore(self.path)
        for i in range(5):
            store.append_record({"request_id": "R%d" % i})
        loaded = store.load_records()
        self.assertEqual([r["request_id"] for r in loaded],
                         ["R0", "R1", "R2", "R3", "R4"])


class TestService(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "store.jsonl")
        self.store = LogStore(self.path)
        self.clock = ManualClock()
        self.svc = ObservabilityService(store=self.store, clock=self.clock)

    def tearDown(self):
        self.tmp.cleanup()

    def test_service_record_correctness_hand_computed_cost(self):
        # Prompt "abcd" -> proxy 1 token. Completion "abcdefgh" -> 2 tokens.
        # alpha-small: (1/1000)*0.10 + (2/1000)*0.20 = 0.0001 + 0.0004 = 0.0005
        result = self.svc.handle_request(
            "T01", "abcd", "alpha-small", prompt_version="v1",
            model_version="v1", completion_text="abcdefgh",
            simulated_latency_ms=100)
        self.assertEqual(result["prompt_tokens"], 1)
        self.assertEqual(result["completion_tokens"], 2)
        self.assertEqual(result["total_tokens"], 3)
        self.assertEqual(result["cost_usd"], 0.0005)
        self.assertEqual(result["latency_ms"], 100)
        self.assertEqual(result["model"], "alpha-small")

    def test_service_persists_record_and_spans(self):
        self.svc.handle_request(
            "T02", "hello world prompt", "alpha-large",
            completion_text="a completion", simulated_latency_ms=200)
        records, spans, corrupt = self.store.load_all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["request_id"], "T02")
        self.assertEqual(len(spans), 3)
        self.assertEqual(corrupt, 0)

    def test_span_parent_child_structure(self):
        result = self.svc.handle_request(
            "T03", "some prompt text", "alpha-small",
            completion_text="reply", simulated_latency_ms=50)
        spans = result["spans"]
        self.assertEqual(len(spans), 3)
        roots = [s for s in spans if s["parent_id"] is None]
        self.assertEqual(len(roots), 1)
        root = roots[0]
        self.assertEqual(root["duration_ms"], 50)
        children = [s for s in spans if s["parent_id"] == root["span_id"]]
        self.assertEqual(len(children), 2)
        self.assertEqual(sorted(root["children"]),
                         sorted([c["span_id"] for c in children]))
        names = [c["name"] for c in children]
        self.assertIn("prepare", names)
        self.assertTrue(any(n.startswith("model_call") for n in names))

    def test_service_multiple_requests_aggregate(self):
        self.svc.handle_request("A1", "abcd", "alpha-small",
                                completion_text="abcdefgh",
                                simulated_latency_ms=100)
        self.svc.handle_request("A2", "abcd", "alpha-small",
                                completion_text="abcdefgh",
                                simulated_latency_ms=300)
        records = self.store.load_records()
        summary = aggregate(records)
        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["total_tokens"], 6)
        self.assertEqual(summary["total_cost_usd"], 0.001)
        self.assertEqual(summary["mean_latency_ms"], 200.0)
        self.assertEqual(summary["p50_latency_ms"], 100)
        self.assertEqual(summary["p95_latency_ms"], 300)

    def test_service_default_completion_is_deterministic_shape(self):
        r1 = self.svc.handle_request("D1", "prompt one", "alpha-small",
                                     simulated_latency_ms=120)
        self.assertTrue(r1["completion_text"])
        self.assertEqual(r1["total_tokens"],
                         r1["prompt_tokens"] + r1["completion_tokens"])


class TestRegistryDiff(unittest.TestCase):
    def test_diff_text_added_line(self):
        d = diff_text("line one\nline two", "line one\nline two\nline three")
        self.assertEqual(d["added"], ["line three"])
        self.assertEqual(d["removed"], [])
        self.assertEqual(d["unchanged"], 2)

    def test_diff_text_removed_and_changed(self):
        d = diff_text("a\nb\nc", "a\nx\nc")
        self.assertEqual(d["added"], ["x"])
        self.assertEqual(d["removed"], ["b"])
        self.assertEqual(d["unchanged"], 2)

    def test_diff_entries_dict_fields(self):
        d = diff_entries({"a": 1, "b": 2, "c": 3},
                         {"a": 1, "b": 99, "d": 4})
        self.assertEqual(d["added_fields"], ["d"])
        self.assertEqual(d["removed_fields"], ["c"])
        self.assertEqual(d["changed_fields"], {"b": {"old": 2, "new": 99}})
        self.assertEqual(d["unchanged_fields"], ["a"])

    def test_registry_diff_prompts(self):
        reg = VersionRegistry()
        reg.register("prompt", "p", "v1", "Answer briefly.\nUse plain language.")
        reg.register("prompt", "p", "v2",
                     "Answer briefly.\nCite sources.\nUse plain language.")
        result = registry_diff(reg, "prompt", "p", "v1", "v2")
        self.assertEqual(result["old_version"], "v1")
        self.assertEqual(result["new_version"], "v2")
        self.assertEqual(result["diff"]["added"], ["Cite sources."])
        self.assertEqual(result["diff"]["removed"], [])


class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "store.jsonl")
        self.store = LogStore(self.path)
        self.clock = ManualClock()
        self.svc = ObservabilityService(store=self.store, clock=self.clock)

    def tearDown(self):
        self.tmp.cleanup()

    def _fill(self):
        self.svc.handle_request("X1", "abcd", "alpha-small",
                                completion_text="abcdefgh",
                                simulated_latency_ms=100)
        self.svc.handle_request("X2", "abcd", "alpha-small",
                                completion_text="abcdefgh",
                                simulated_latency_ms=300)

    def test_dashboard_contains_exact_totals(self):
        self._fill()
        records, spans, _ = self.store.load_all()
        summary = aggregate(records)
        doc = generate_dashboard(records, spans)
        self.assertIn("<td>%d</td>" % summary["count"], doc)
        self.assertIn(str(summary["total_tokens"]), doc)
        self.assertIn(str(summary["p50_latency_ms"]), doc)
        self.assertIn(str(summary["p95_latency_ms"]), doc)
        self.assertIn("alpha-small", doc)
        self.assertIn("X1", doc)
        self.assertIn("X2", doc)

    def test_dashboard_writes_file(self):
        self._fill()
        records, spans, _ = self.store.load_all()
        out = os.path.join(self.tmp.name, "dash.html")
        doc = generate_dashboard(records, spans, output_path=out)
        self.assertTrue(os.path.exists(out))
        with open(out, encoding="utf-8") as f:
            self.assertEqual(f.read(), doc)

    def test_aggregation_correctness_per_model(self):
        self.svc.handle_request("M1", "abcd", "alpha-small",
                                completion_text="abcdefgh",
                                simulated_latency_ms=100)
        self.svc.handle_request("M2", "abcdefgh", "alpha-large",
                                completion_text="abcd",
                                simulated_latency_ms=400)
        records = self.store.load_records()
        summary = aggregate(records)
        # alpha-large: prompt proxy ceil(8/4)=2, completion ceil(4/4)=1
        # cost = (2/1000)*0.50 + (1/1000)*1.00 = 0.001 + 0.001 = 0.002
        self.assertEqual(summary["per_model"]["alpha-large"]["total_cost_usd"], 0.002)
        self.assertEqual(summary["per_model"]["alpha-small"]["count"], 1)
        self.assertEqual(summary["count"], 2)


if __name__ == "__main__":
    unittest.main()
