"""
Request logging and metrics (admin sprint).

log_query writes one row per /chat request into query_logs. It is deliberately
best-effort: any failure is swallowed, because analytics must never break a
passenger's reply. metrics() and recent() aggregate that table for the admin
monitoring dashboard, and are also the measurement source for the Chapter 5
evaluation (latency against the <3s NFR, grounding rate, route distribution).
"""
from __future__ import annotations


async def log_query(pool, *, session_id, route, message, latency_ms,
                    grounded=None, top_similarity=None, outcome=None) -> None:
    try:
        await pool.execute(
            "insert into public.query_logs "
            "(session_id, route, message, grounded, top_similarity, outcome, latency_ms) "
            "values ($1, $2, $3, $4, $5, $6, $7)",
            session_id, route, message, grounded, top_similarity, outcome, latency_ms,
        )
    except Exception:
        # Logging is non-critical; never let it affect the response.
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


async def recent(pool, limit: int = 50) -> list[dict]:
    rows = await pool.fetch(
        "select created_at, route, message, grounded, outcome, latency_ms "
        "from public.query_logs order by created_at desc limit $1", limit)
    return [{"created_at": r["created_at"].isoformat(), "route": r["route"],
             "message": r["message"], "grounded": r["grounded"],
             "outcome": r["outcome"], "latency_ms": r["latency_ms"]} for r in rows]