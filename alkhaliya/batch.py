from __future__ import annotations

import json
import statistics
import time
import tracemalloc
from pathlib import Path

from .engine import run_workflow


def _p(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round((pct / 100) * (len(ordered) - 1))))]


def evaluate(workflow: dict, events_path: str | Path, *, repeat: int = 1) -> dict:
    events = [json.loads(line) for line in Path(events_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    ok = errors = 0
    queues: dict[str, int] = {}
    latencies = []
    started = time.perf_counter()
    tracemalloc.start()
    for _ in range(repeat):
        for event in events:
            result = run_workflow(workflow, event, dry_run=True)
            if result["ok"]:
                ok += 1
                queue = str(result["state"].get("queue") or "")
                queues[queue] = queues.get(queue, 0) + 1
            else:
                errors += 1
            latencies.append(float(result.get("elapsed_ms") or 0.0))
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    processed = len(events) * repeat
    return {
        "events": str(Path(events_path).resolve()),
        "records": len(events),
        "repeat": repeat,
        "processed": processed,
        "ok": ok,
        "errors": errors,
        "success_rate": ok / processed if processed else 0.0,
        "queues": queues,
        "latency_ms": {"mean": statistics.fmean(latencies) if latencies else 0.0, "p99": _p(latencies, 99), "max": max(latencies) if latencies else 0.0},
        "memory_mb": {"current": current / 1_000_000, "peak": peak / 1_000_000},
        "elapsed_seconds": time.perf_counter() - started,
        "collapse_check": {"passed": errors == 0, "criteria": "errors == 0"},
    }

