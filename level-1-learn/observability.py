"""Level 1 Learn: LLM observability primitives, stdlib only.

Three pieces, matching the SPEC v1 core for P12:
1. RequestLogger: one structured record per request (prompt, model,
   tokens, cost, latency), with cost computed from a stated price table.
2. Tracer: spans with parent and child links and durations, driven by
   an injected clock so tests are deterministic.
3. VersionRegistry: prompt and model versions, resolve and changelog.
Plus aggregate(): summary statistics over a list of log records.

The price table below holds teaching constants stated for this level.
They are not live vendor prices and must not be quoted as such.
All data in this level is simulated. No real LLM is called.
"""
import hashlib
import json
import math

# Dollars per 1,000 tokens. Teaching constants, stated in the README.
PRICE_TABLE = {
    "alpha-small": {"input_per_1k": 0.10, "output_per_1k": 0.20},
    "alpha-large": {"input_per_1k": 0.50, "output_per_1k": 1.00},
}


class ObservabilityError(ValueError):
    """Raised on invalid input to any observability primitive."""


def compute_cost(model, prompt_tokens, completion_tokens, price_table=None):
    """Cost in USD for one request, rounded to 6 decimal places.

    cost = (prompt_tokens / 1000) * input_per_1k
         + (completion_tokens / 1000) * output_per_1k
    """
    table = PRICE_TABLE if price_table is None else price_table
    if model not in table:
        raise ObservabilityError("unknown model: " + str(model))
    if prompt_tokens < 0 or completion_tokens < 0:
        raise ObservabilityError("token counts must be non-negative")
    rates = table[model]
    cost = (prompt_tokens / 1000.0) * rates["input_per_1k"] \
        + (completion_tokens / 1000.0) * rates["output_per_1k"]
    return round(cost, 6)


def prompt_hash(prompt):
    """Full sha256 hex digest of the prompt text (UTF-8)."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


class RequestLogger:
    """Collects one structured record per simulated request."""

    def __init__(self, price_table=None):
        self.price_table = PRICE_TABLE if price_table is None else price_table
        self.records = []

    def log_request(self, request_id, prompt, model, prompt_tokens,
                    completion_tokens, latency_ms,
                    prompt_version=None, model_version=None):
        if not isinstance(prompt, str) or not prompt:
            raise ObservabilityError("prompt must be a non-empty string")
        if latency_ms < 0:
            raise ObservabilityError("latency_ms must be non-negative")
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
        }
        self.records.append(record)
        return record

    def to_json_lines(self):
        """All records as JSON lines (one JSON object per line)."""
        return "\n".join(
            json.dumps(r, sort_keys=True) for r in self.records)


class ManualClock:
    """Deterministic clock for tests and the runner.

    now() returns the current value in ms. advance(ms) moves it forward.
    """

    def __init__(self, start_ms=0):
        self._now = start_ms

    def now(self):
        return self._now

    def advance(self, ms):
        if ms < 0:
            raise ObservabilityError("clock cannot move backwards")
        self._now += ms
        return self._now


class Span:
    """One trace span. Use as a context manager via Tracer.span()."""

    def __init__(self, tracer, name, parent_id):
        self._tracer = tracer
        self.name = name
        self.parent_id = parent_id
        self.span_id = None
        self.start_ms = None
        self.end_ms = None
        self.duration_ms = None
        self.children = []

    def __enter__(self):
        tracer = self._tracer
        self.span_id = tracer._next_id()
        self.start_ms = tracer.clock()
        if self.parent_id is not None:
            tracer._spans[self.parent_id].children.append(self.span_id)
        tracer._spans[self.span_id] = self
        tracer._stack.append(self.span_id)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.end_ms = self._tracer.clock()
        self.duration_ms = self.end_ms - self.start_ms
        self._tracer._stack.pop()
        return False

    def to_dict(self):
        return {
            "span_id": self.span_id,
            "name": self.name,
            "parent_id": self.parent_id,
            "children": list(self.children),
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "duration_ms": self.duration_ms,
        }


class Tracer:
    """Creates spans with deterministic ids (span-1, span-2, ...).

    clock is a zero-argument callable returning the current time in ms.
    Inject ManualClock.now in tests and in the runner for determinism.
    """

    def __init__(self, clock):
        self.clock = clock
        self._counter = 0
        self._spans = {}
        self._stack = []

    def _next_id(self):
        self._counter += 1
        return "span-" + str(self._counter)

    def span(self, name):
        parent_id = self._stack[-1] if self._stack else None
        return Span(self, name, parent_id)

    def spans(self):
        """All finished and open spans as dicts, in creation order."""
        return [self._spans[k].to_dict() for k in sorted(
            self._spans, key=lambda s: int(s.split("-")[1]))]

    def roots(self):
        return [s for s in self.spans() if s["parent_id"] is None]


class VersionRegistry:
    """Registers prompt and model versions. In-memory only.

    register(kind, name, version, content) stores one version.
    Registering the same kind, name, and version twice raises.
    resolve(kind, name, version=None) returns the named version, or
    the most recently registered version when version is None.
    """

    KINDS = ("prompt", "model")

    def __init__(self):
        self._entries = {}  # (kind, name) -> list of entry dicts
        self._changelog = []

    def register(self, kind, name, version, content):
        if kind not in self.KINDS:
            raise ObservabilityError("kind must be prompt or model")
        if not name or not version:
            raise ObservabilityError("name and version are required")
        key = (kind, name)
        entries = self._entries.setdefault(key, [])
        if any(e["version"] == version for e in entries):
            raise ObservabilityError(
                "duplicate version: %s/%s %s" % (kind, name, version))
        entry = {"kind": kind, "name": name, "version": version,
                 "content": content}
        entries.append(entry)
        self._changelog.append({"kind": kind, "name": name,
                                "version": version})
        return entry

    def resolve(self, kind, name, version=None):
        entries = self._entries.get((kind, name))
        if not entries:
            raise ObservabilityError(
                "unknown %s: %s" % (kind, name))
        if version is None:
            return entries[-1]
        for e in entries:
            if e["version"] == version:
                return e
        raise ObservabilityError(
            "unknown version: %s/%s %s" % (kind, name, version))

    def list_versions(self, kind, name):
        entries = self._entries.get((kind, name), [])
        return [e["version"] for e in entries]

    def changelog(self):
        """Registration events in order, as dicts (kind, name, version)."""
        return [dict(c) for c in self._changelog]


def percentile(values, p):
    """Nearest-rank percentile. p is 0 to 100.

    rank = ceil(p / 100 * n), 1-indexed into the sorted values.
    """
    if not values:
        raise ObservabilityError("percentile of an empty list")
    if p < 0 or p > 100:
        raise ObservabilityError("p must be between 0 and 100")
    ordered = sorted(values)
    rank = math.ceil(p / 100.0 * len(ordered))
    rank = max(1, min(rank, len(ordered)))
    return ordered[rank - 1]


def _summarize(records):
    lat = [r["latency_ms"] for r in records]
    return {
        "count": len(records),
        "prompt_tokens": sum(r["prompt_tokens"] for r in records),
        "completion_tokens": sum(r["completion_tokens"] for r in records),
        "total_tokens": sum(r["total_tokens"] for r in records),
        "total_cost_usd": round(sum(r["cost_usd"] for r in records), 6),
        "mean_latency_ms": round(sum(lat) / len(lat), 3) if lat else 0,
        "p50_latency_ms": percentile(lat, 50) if lat else 0,
        "p95_latency_ms": percentile(lat, 95) if lat else 0,
    }


def aggregate(records):
    """Summary over log records, overall and per model."""
    if not records:
        empty = {"count": 0, "prompt_tokens": 0, "completion_tokens": 0,
                 "total_tokens": 0, "total_cost_usd": 0,
                 "mean_latency_ms": 0, "p50_latency_ms": 0,
                 "p95_latency_ms": 0}
        return dict(empty, per_model={})
    summary = _summarize(records)
    per_model = {}
    for model in sorted({r["model"] for r in records}):
        per_model[model] = _summarize(
            [r for r in records if r["model"] == model])
    summary["per_model"] = per_model
    return summary
