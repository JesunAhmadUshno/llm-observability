"""Unit tests for Level 4 Live: corpus integrity, the recorder with a
stub model client, the client rotation, and the analyzer on fixture
records. No network and no real model: the live run itself is the
evidence for those, in results_live.json."""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "level-4-live"))
sys.path.insert(0, os.path.join(ROOT, "level-2-build"))

from analyze import analyze  # noqa: E402
from client import build_rotation  # noqa: E402
from live import LiveRecorder, answer_check, iter_questions, load_corpus  # noqa: E402
from service import LogStore  # noqa: E402

CORPUS = load_corpus()


class StubClient:
    """Stands in for ModelClient: returns a canned real-shaped reply."""

    def __init__(self, text="The answer is 0.25.", fail=False):
        self.text = text
        self.fail = fail

    def chat(self, messages, max_tokens=160):
        if self.fail:
            raise TimeoutError("stub timeout")
        return {"completion_text": self.text, "prompt_tokens": 100,
                "completion_tokens": 6, "usage_present": True}

    def tokenize(self, text):
        return len(text.split())


def first_pair():
    return iter_questions(CORPUS)[0]


class TestCorpus(unittest.TestCase):
    def test_answers_are_in_their_documents(self):
        pairs = iter_questions(CORPUS)
        self.assertGreaterEqual(len(CORPUS["documents"]), 10)
        self.assertGreaterEqual(len(pairs), 20)
        for doc, q in pairs:
            self.assertIn(q["expected_answer"].lower(), doc["text"].lower(),
                          q["id"])

    def test_ids_unique(self):
        doc_ids = [d["id"] for d in CORPUS["documents"]]
        q_ids = [q["id"] for _d, q in iter_questions(CORPUS)]
        self.assertEqual(len(doc_ids), len(set(doc_ids)))
        self.assertEqual(len(q_ids), len(set(q_ids)))


class TestAnswerCheck(unittest.TestCase):
    def test_check(self):
        self.assertTrue(answer_check("It is 0.25 exactly.", "0.25"))
        self.assertTrue(answer_check("ABOVE 0.25", "0.25"))
        self.assertFalse(answer_check("It is 0.5.", "0.25"))
        self.assertFalse(answer_check("", "0.25"))


class TestRecorder(unittest.TestCase):
    def test_ok_request_is_recorded_with_spans(self):
        doc, q = first_pair()
        with tempfile.TemporaryDirectory() as td:
            store = LogStore(os.path.join(td, "store.jsonl"))
            recorder = LiveRecorder(store, StubClient())
            record = recorder.ask("live-0001", doc, q)
            self.assertEqual(record["status"], "ok")
            self.assertEqual(record["prompt_tokens"], 100)
            self.assertEqual(record["total_tokens"], 106)
            self.assertEqual(record["cost_usd"], 0.0)
            self.assertGreaterEqual(record["latency_ms"], 0)
            self.assertTrue(record["answer_check_pass"])  # stub says 0.25
            records, spans, corrupt = store.load_all()
            self.assertEqual(len(records), 1)
            self.assertEqual(corrupt, 0)
            self.assertEqual(len(spans), record["span_count"])
            self.assertGreaterEqual(len(spans), 3)

    def test_model_error_is_recorded_not_raised(self):
        doc, q = first_pair()
        with tempfile.TemporaryDirectory() as td:
            store = LogStore(os.path.join(td, "store.jsonl"))
            recorder = LiveRecorder(store, StubClient(fail=True))
            record = recorder.ask("live-0002", doc, q)
            self.assertEqual(record["status"], "error")
            self.assertIn("TimeoutError", record["error"])
            self.assertFalse(record["answer_check_pass"])
            self.assertEqual(len(store.load_records()), 1)


class TestRotation(unittest.TestCase):
    def test_deterministic_and_complete(self):
        questions = iter_questions(CORPUS)
        a = build_rotation(questions, 42)
        b = build_rotation(questions, 42)
        self.assertEqual(a, b)
        self.assertEqual(sorted(a), sorted(q["id"] for _d, q in questions))


def fixture_record(i, latency, status="ok", passed=True, ts=None):
    return {
        "request_id": "live-%04d" % i,
        "timestamp_utc": ts or "2026-11-15T00:00:%02d+00:00" % i,
        "model": "stub",
        "prompt_tokens": 100,
        "completion_tokens": 10,
        "total_tokens": 110,
        "cost_usd": 0.0,
        "latency_ms": latency,
        "status": status,
        "error": None if status == "ok" else "TimeoutError: stub",
        "answer_check_pass": passed,
        "question_id": "q-%d" % i,
        "token_source": "usage",
        "prompt_chars": 400,
        "completion_chars": 40,
    }


class TestAnalyze(unittest.TestCase):
    def test_counts_percentiles_and_error_rate(self):
        records = [fixture_record(i, (i + 1) * 10) for i in range(10)]
        records.append(fixture_record(99, 5, status="error", passed=False,
                                      ts="2026-11-15T00:00:10+00:00"))
        out = analyze(records, {"host": "test"})
        self.assertEqual(out["requests"]["total"], 11)
        self.assertEqual(out["requests"]["ok"], 10)
        self.assertEqual(out["requests"]["errors"], 1)
        self.assertEqual(out["requests"]["error_rate"], round(1 / 11, 6))
        self.assertEqual(out["latency_ms"]["mean_ms"], 55.0)
        self.assertEqual(out["latency_ms"]["p50_ms"], 50)
        self.assertEqual(out["latency_ms"]["p95_ms"], 100)
        self.assertEqual(out["latency_ms"]["p99_ms"], 100)
        self.assertEqual(out["tokens"]["total"], 1100)
        self.assertEqual(out["answer_check"]["overall"]["pass_rate"], 1.0)
        self.assertEqual(out["answer_check"]["by_question"]["q-0"]["pass_rate"], 1.0)
        self.assertEqual(out["window"]["duration_s"], 10.0)
        self.assertIn("latency_ms", out["drift_first_vs_second_half"])
        self.assertTrue(any(c["kind"] == "error"
                            for c in out["anomaly_candidates"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
