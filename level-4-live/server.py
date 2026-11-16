"""Level 4 Live: the instrumented document-question service.

An HTTP front end over LiveRecorder. POST /ask with a JSON body of
{"question_id": "..."} runs one real model call for that bundled
question and returns the observability record (without the prompt and
completion text, which live in the store). GET /health returns the
service state and the number of records stored so far.

Configuration is by environment:
- LIVE_MODEL_URL: model server base URL (default http://127.0.0.1:18080)
- LIVE_PORT: port to bind on 127.0.0.1 (default 18081)
- LIVE_STORE_PATH: JSONL store path (default ./store_live.jsonl)

The service binds to localhost only. It exists to be observed, on one
fleet machine, for one measured window; it is not a public service.
"""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from live import LiveRecorder, ModelClient, iter_questions, load_corpus

# live.py puts level-2-build on sys.path when it is imported.
from service import LogStore  # noqa: E402

STORE_PATH = os.environ.get("LIVE_STORE_PATH", "store_live.jsonl")
MODEL_URL = os.environ.get("LIVE_MODEL_URL", "http://127.0.0.1:18080")
PORT = int(os.environ.get("LIVE_PORT", "18081"))

CORPUS = load_corpus()
QUESTIONS = {q["id"]: (d, q) for d, q in iter_questions(CORPUS)}

STORE = LogStore(STORE_PATH)
RECORDER = LiveRecorder(STORE, ModelClient(MODEL_URL))
LOCK = threading.Lock()
COUNTER = {"n": 0}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep stdout for the run log lines below
        pass

    def _send_json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            records = STORE.load_records()
            self._send_json(200, {"ok": True, "records": len(records)})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/ask":
            self._send_json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            question_id = body["question_id"]
        except Exception as exc:
            self._send_json(400, {"error": "bad request: " + str(exc)[:120]})
            return
        if question_id not in QUESTIONS:
            self._send_json(404, {"error": "unknown question_id"})
            return
        document, question = QUESTIONS[question_id]
        with LOCK:
            COUNTER["n"] += 1
            request_id = "live-%04d" % COUNTER["n"]
            record = RECORDER.ask(request_id, document, question)
        print("served %s %s status=%s latency_ms=%s pass=%s" % (
            request_id, question_id, record["status"],
            record["latency_ms"], record["answer_check_pass"]), flush=True)
        self._send_json(200 if record["status"] == "ok" else 502, {
            "request_id": request_id,
            "question_id": question_id,
            "status": record["status"],
            "error": record["error"],
            "latency_ms": record["latency_ms"],
            "prompt_tokens": record["prompt_tokens"],
            "completion_tokens": record["completion_tokens"],
            "answer_check_pass": record["answer_check_pass"],
            "completion_text": record["completion_text"],
        })


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("live service on 127.0.0.1:%d model=%s store=%s" % (
        PORT, MODEL_URL, STORE_PATH), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
