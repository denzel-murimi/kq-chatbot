"""
Lightweight per-stage timing for the /chat request (performance instrumentation).

Usage:
    timer = StageTimer()
    with timer.track("classify"):
        ...work...
    ...
    await analytics.log_query(..., timings=timer.as_dict())

Each stage records its wall-clock duration in whole milliseconds. Timing is
best-effort and adds negligible overhead; it never changes behaviour.
"""
from __future__ import annotations

import time
from contextlib import contextmanager


class StageTimer:
    def __init__(self) -> None:
        self._stages: dict[str, int] = {}

    @contextmanager
    def track(self, name: str):
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self._stages[name] = int((time.perf_counter() - t0) * 1000)

    def merge(self, extra: dict | None) -> None:
        """Fold in sub-stage timings returned by a called module (e.g. RAG)."""
        if extra:
            for k, v in extra.items():
                try:
                    self._stages[k] = int(v)
                except (TypeError, ValueError):
                    pass

    def as_dict(self) -> dict:
        return dict(self._stages)