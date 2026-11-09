"""
Request logging and metrics (admin sprint; extended with per-stage timings).

log_query writes one row per /chat request into query_logs, now including an
optional per-stage latency breakdown (timings). It is best-effort: any failure
is swallowed, because analytics must never break a passenger's reply. metrics()
and recent() aggregate the table for the admin dashboard; stage_latencies()
returns the average time spent in each stage, to locate the latency bottleneck.
"""
from __future__ import annotations

import json


async def log_query(pool, *, session_id, route, message, latency_ms,
                    grounded=None, top_similarity=None, outcome=None, timings=None) -> None:
    try:
        await pool.execute(
            "insert into public.query_logs "
            "(session_id, route, message, grounded, top_similarity, outcome, latency_ms, timings) "
            "values ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)",
            session_id, route, message, grounded, top_similarity, outcome, latency_ms,
            json.dumps(timings) if timings else None,
        )
    except Exception:
        pass


async def metrics(pool) -> dict:
    total = await pool.fetchval("select count(*) from public.query_logs") or 0
    by_route = {
        r["route"]: r["n"]
        for r in await pool.fetch(
            "select route, count(*) as n from public.query_logs group by route order by n desc")
    }
    lat = await pool.fetchrow(
        "select coalesce(avg(latency_ms), 0)::int as avg_ms, "
        "coalesce(percentile_cont(0.95) within group (order by latency_ms), 0)::int as p95_ms "
        "from public.query_logs")
    g = await pool.fetchrow(
        "select count(*) filter (where route = 'informational') as informational, "
        "count(*) filter (where route = 'informational' and grounded) as grounded "
        "from public.query_logs")
    informational = g["informational"] or 0
    grounded = g["grounded"] or 0
    return {
        "total_queries": total,
        "by_route": by_route,
        "avg_latency_ms": lat["avg_ms"],
        "p95_latency_ms": lat["p95_ms"],
        "informational_queries": informational,
        "grounded_queries": grounded,
        "grounded_rate": round(grounded / informational, 3) if informational else None,
    }


async def stage_latencies(pool) -> dict:
    """Average milliseconds per stage across all logged requests that carried a
    timing breakdown. Keys vary by request, so they are aggregated in Python."""
    rows = await pool.fetch("select timings from public.query_logs where timings is not null")
    sums: dict[str, int] = {}
    counts: dict[str, int] = {}
    for r in rows:
        raw = r["timings"]
        data = json.loads(raw) if isinstance(raw, str) else (raw or {})
        for k, v in data.items():
            try:
                sums[k] = sums.get(k, 0) + int(v)
                counts[k] = counts.get(k, 0) + 1
            except (TypeError, ValueError):
                continue
    return {k: round(sums[k] / counts[k]) for k in sums if counts[k]}


async def recent(pool, limit: int = 50) -> list[dict]:
    rows = await pool.fetch(
        "select created_at, route, message, grounded, outcome, latency_ms "
        "from public.query_logs order by created_at desc limit $1", limit)
    return [{"created_at": r["created_at"].isoformat(), "route": r["route"],
             "message": r["message"], "grounded": r["grounded"],
             "outcome": r["outcome"], "latency_ms": r["latency_ms"]} for r in rows]