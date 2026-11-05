"""Level 2 Build: persistent LLM observability service, stdlib only.

Pieces:
1. LogStore: persistent JSONL store for records and spans.
   One file, each line is a JSON object tagged with "type" as
   "record" or "span". Corrupt lines are skipped on load and counted.
2. ObservabilityService.handle_request: runs a simulated model call
   through nested trace spans, computes token counts with a
   deterministic proxy, computes cost from the Learn price table,
   takes latency from an injected clock, persists record and spans,
   and returns the record.
3. Registry diff: diff_text, diff_entries, and registry_diff extend
   the Learn VersionRegistry with added, removed, and changed lines
   or fields between two versions.
4. Dashboard: generate_dashboard builds a static HTML dashboard from
   stored records with totals, a per-model table, p50 and p95
   latency, and a trace and request list.

Token proxy, stated plainly: this is a proxy, not a real tokenizer.
proxy_token_count(text) = ceil(len(text) / 4), with a minimum of 1
for non-empty text and 0 for empty text. It approximates the common
rule of thumb of about 4 characters per token. It must not be quoted
as a real tokenizer count for any model.

Price table and cost formula are reused from Level 1 Learn.
All model calls in this level are simulated. No real LLM is called.
"""
import difflib
import html
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEARN_DIR = os.path.join(os.path.dirname(HERE), "level-1-learn")
if LEARN_DIR not in sys.path:
    sys.path.insert(0, LEARN_DIR)

from observability import (  # noqa: E402
    PRICE_TABLE,
    ManualClock,
    ObservabilityError,
    Tracer,
    VersionRegistry,
    aggregate,
    compute_cost,
    prompt_hash,
)

__all__ = [
    "PRICE_TABLE",
    "LogStore",
    "ObservabilityService",
    "proxy_token_count",
    "diff_text",
    "diff_entries",
    "registry_diff",
    "generate_dashboard",
]


def proxy_token_count(text):
    """Deterministic token proxy: ceil(len(text) / 4).

    This is a proxy, not a real tokenizer. Empty text returns 0,
    non-empty text returns at least 1.
    """
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4.0))


class LogStore:
    """Persistent JSONL store for records and spans.

    Each line in the file is {"type": "record", "data": {...}} or
    {"type": "span", "data": {...}}. Append methods write one line
    each. Load methods skip corrupt lines and record how many were
    skipped in self.last_corrupt_count after a load.
    """

    def __init__(self, path):
        self.path = path
        self.last_corrupt_count = 0

    def _append(self, kind, data):
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        line = json.dumps({"type": kind, "data": data}, sort_keys=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def append_record(self, record):
        self._append("record", record)

    def append_span(self, span):
        self._append("span", span)

    def append_spans(self, spans):
        for span in spans:
            self.append_span(span)

    def _load(self, want_type):
        items = []
        corrupt = 0
        if not os.path.exists(self.path):
            self.last_corrupt_count = 0
            return items
        with open(self.path, encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except (ValueError, TypeError):
                    corrupt += 1
                    continue
                if not isinstance(obj, dict) or "type" not in obj or "data" not in obj:
                    corrupt += 1
                    continue
                if obj["type"] == want_type:
                    items.append(obj["data"])
        self.last_corrupt_count = corrupt
        return items

    def load_records(self):
        return self._load("record")

    def load_spans(self):
        return self._load("span")

    def load_all(self):
        """Return (records, spans, corrupt_count)."""
        records = self._load("record")
        corrupt_after_records = self.last_corrupt_count
        spans = self._load("span")
        # Both passes scan the same file, so corrupt count is the
        # same; keep the value from the second pass for consistency.
        corrupt = self.last_corrupt_count
        _ = corrupt_after_records
        return records, spans, corrupt

    def clear(self):
        if os.path.exists(self.path):
            os.remove(self.path)
        self.last_corrupt_count = 0


class ObservabilityService:
    """Simulated end-to-end observability service.

    clock is a ManualClock (or any object with now() and advance()).
    Latency for a request is the duration of its root span, which is
    exactly the sum of advances inside the request, so it is fully
    deterministic when the caller supplies simulated_latency_ms.
    """

    def __init__(self, store, registry=None, clock=None, price_table=None):
        self.store = store
        self.registry = registry if registry is not None else VersionRegistry()
        self.clock = clock if clock is not None else ManualClock()
        self.price_table = PRICE_TABLE if price_table is None else price_table

    def handle_request(self, request_id, prompt, model,
                       prompt_version=None, model_version=None,
                       completion_text=None, simulated_latency_ms=120):
        if not isinstance(prompt, str) or not prompt:
            raise ObservabilityError("prompt must be a non-empty string")
        if simulated_latency_ms < 0:
            raise ObservabilityError("latency must be non-negative")
        if completion_text is None:
            completion_text = (
                "Simulated completion for request " + str(request_id)
                + " using model " + str(model) + "."
            )
        # Nested spans: root plus at least 2 child spans.
        tracer = Tracer(self.clock.now)
        # Split latency deterministically: prepare gets one fifth,
        # model_call gets the rest. Root duration equals the total.
        prepare_ms = simulated_latency_ms // 5
        model_ms = simulated_latency_ms - prepare_ms
        with tracer.span("request:" + str(request_id)) as root:
            with tracer.span("prepare"):
                self.clock.advance(prepare_ms)
            with tracer.span("model_call:" + str(model)):
                self.clock.advance(model_ms)
            latency_ms = root.duration_ms
            # duration_ms is set on exit; inside the block compute it
            # as the intended total, which equals the sum of advances.
            latency_ms = simulated_latency_ms
        # After exit, root duration is authoritative and must match.
        spans = tracer.spans()
        root_span = [s for s in spans if s["parent_id"] is None][0]
        latency_ms = root_span["duration_ms"]
        prompt_tokens = proxy_token_count(prompt)
        completion_tokens = proxy_token_count(completion_text)
        cost = compute_cost(model, prompt_tokens, completion_tokens,
                            self.price_table)
        record = {
            "request_id": request_id,
            "prompt": prompt,
            "prompt_hash": prompt_hash(prompt),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": cost,
            "latency_ms": latency_ms,
            "prompt_version": prompt_version,
            "model_version": model_version,
            "completion_text": completion_text,
            "trace_root_span_id": root_span["span_id"],
            "span_count": len(spans),
        }
        self.store.append_record(record)
        self.store.append_spans(spans)
        # Attach spans to the returned record copy for callers, but
        # keep the persisted record as the plain record above.
        result = dict(record)
        result["spans"] = spans
        return result


def diff_text(old_text, new_text):
    """Line diff between two text contents.

    Returns {"added": [...], "removed": [...], "unchanged": int}.
    Lines are compared without trailing newlines.
    """
    old_lines = str(old_text).splitlines()
    new_lines = str(new_text).splitlines()
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines)
    added = []
    removed = []
    unchanged = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            unchanged += (i2 - i1)
        elif tag == "delete":
            removed.extend(old_lines[i1:i2])
        elif tag == "insert":
            added.extend(new_lines[j1:j2])
        elif tag == "replace":
            removed.extend(old_lines[i1:i2])
            added.extend(new_lines[j1:j2])
    return {"added": added, "removed": removed, "unchanged": unchanged}


def diff_entries(old_content, new_content):
    """Diff two version contents.

    If both contents are dicts, diff by fields: added_fields,
    removed_fields, changed_fields (field -> {"old":..., "new":...}),
    and unchanged_fields. If both are strings, delegate to diff_text
    and wrap the result. Mixed types are reported as a full change.
    """
    if isinstance(old_content, dict) and isinstance(new_content, dict):
        old_keys = set(old_content.keys())
        new_keys = set(new_content.keys())
        changed = {}
        unchanged_fields = []
        for key in sorted(old_keys & new_keys):
            if old_content[key] != new_content[key]:
                changed[key] = {"old": old_content[key],
                                "new": new_content[key]}
            else:
                unchanged_fields.append(key)
        return {
            "added_fields": sorted(new_keys - old_keys),
            "removed_fields": sorted(old_keys - new_keys),
            "changed_fields": changed,
            "unchanged_fields": unchanged_fields,
        }
    if isinstance(old_content, str) and isinstance(new_content, str):
        line_diff = diff_text(old_content, new_content)
        return {
            "added": line_diff["added"],
            "removed": line_diff["removed"],
            "unchanged": line_diff["unchanged"],
        }
    return {
        "added": [new_content],
        "removed": [old_content],
        "unchanged": 0,
    }


def registry_diff(registry, kind, name, old_version, new_version):
    """Diff two registered versions from a VersionRegistry."""
    old_entry = registry.resolve(kind, name, old_version)
    new_entry = registry.resolve(kind, name, new_version)
    return {
        "kind": kind,
        "name": name,
        "old_version": old_version,
        "new_version": new_version,
        "diff": diff_entries(old_entry["content"], new_entry["content"]),
    }


def generate_dashboard(records, spans=None, output_path=None):
    """Generate a static HTML dashboard string from stored records.

    Contains the measured totals, a per-model table, p50 and p95
    latency, and a trace and request list. If output_path is given,
    the HTML is also written to that path.
    """
    spans = spans if spans is not None else []
    summary = aggregate(records) if records else {
        "count": 0, "prompt_tokens": 0, "completion_tokens": 0,
        "total_tokens": 0, "total_cost_usd": 0, "mean_latency_ms": 0,
        "p50_latency_ms": 0, "p95_latency_ms": 0, "per_model": {},
    }
    total_cost_str = "%.2f" % summary["total_cost_usd"] if summary["count"] else "0.00"
    # Also keep a precise representation in a data attribute comment
    # so exact totals are searchable.
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en"><head><meta charset="utf-8">')
    parts.append("<title>LLM Observability Dashboard</title></head><body>")
    parts.append("<h1>LLM Observability Dashboard</h1>")
    parts.append("<p>Simulated requests only. No real LLM was called. "
                 "Token counts use the stated proxy, not a real tokenizer.</p>")
    parts.append("<h2>Totals</h2>")
    parts.append("<table>")
    parts.append("<tr><th>Measure</th><th>Value</th></tr>")
    parts.append("<tr><td>Requests</td><td>%d</td></tr>" % summary["count"])
    parts.append("<tr><td>Prompt tokens</td><td>%d</td></tr>" % summary["prompt_tokens"])
    parts.append("<tr><td>Completion tokens</td><td>%d</td></tr>" % summary["completion_tokens"])
    parts.append("<tr><td>Total tokens</td><td>%d</td></tr>" % summary["total_tokens"])
    parts.append("<tr><td>Total cost USD</td><td>%s</td></tr>" % total_cost_str)
    parts.append("<tr><td>Total cost USD (precise)</td><td>%s</td></tr>" % str(summary["total_cost_usd"]))
    parts.append("<tr><td>Mean latency ms</td><td>%s</td></tr>" % str(summary["mean_latency_ms"]))
    parts.append("<tr><td>p50 latency ms</td><td>%s</td></tr>" % str(summary["p50_latency_ms"]))
    parts.append("<tr><td>p95 latency ms</td><td>%s</td></tr>" % str(summary["p95_latency_ms"]))
    parts.append("<tr><td>Spans</td><td>%d</td></tr>" % len(spans))
    parts.append("</table>")
    parts.append("<h2>Per-model</h2>")
    parts.append("<table>")
    parts.append("<tr><th>Model</th><th>Count</th><th>Total tokens</th>"
                 "<th>Cost USD</th><th>Mean latency ms</th>"
                 "<th>p50 ms</th><th>p95 ms</th></tr>")
    for model in sorted(summary.get("per_model", {})):
        m = summary["per_model"][model]
        parts.append(
            "<tr><td>%s</td><td>%d</td><td>%d</td><td>%s</td>"
            "<td>%s</td><td>%s</td><td>%s</td></tr>" % (
                html.escape(str(model)), m["count"], m["total_tokens"],
                str(m["total_cost_usd"]), str(m["mean_latency_ms"]),
                str(m["p50_latency_ms"]), str(m["p95_latency_ms"])))
    parts.append("</table>")
    parts.append("<h2>Requests and traces</h2>")
    parts.append("<ul>")
    for r in records:
        parts.append(
            "<li>%s model=%s tokens=%d cost=%s latency_ms=%s "
            "prompt_version=%s root_span=%s</li>" % (
                html.escape(str(r["request_id"])),
                html.escape(str(r["model"])),
                r["total_tokens"], str(r["cost_usd"]),
                str(r["latency_ms"]),
                html.escape(str(r.get("prompt_version"))),
                html.escape(str(r.get("trace_root_span_id", "")))))
    parts.append("</ul>")
    parts.append("<h2>Spans</h2>")
    parts.append("<ul>")
    for s in spans:
        parts.append(
            "<li>%s name=%s parent=%s duration_ms=%s</li>" % (
                html.escape(str(s.get("span_id"))),
                html.escape(str(s.get("name"))),
                html.escape(str(s.get("parent_id"))),
                str(s.get("duration_ms"))))
    parts.append("</ul>")
    parts.append("</body></html>")
    doc = "\n".join(parts) + "\n"
    if output_path:
        directory = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(directory, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(doc)
    return doc
