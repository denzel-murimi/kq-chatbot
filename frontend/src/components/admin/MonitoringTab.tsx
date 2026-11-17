"use client";

import { useCallback, useEffect, useState } from "react";
import { CircleCheck, CircleMinus, CircleX, Gauge, Timer } from "lucide-react";
import { adminApi, AdminAuthError, type LogRow, type Metrics } from "@/lib/admin-api";
import { Notice, Panel, RefreshButton, Skeleton, UpdatedAt, tableHead, td, th } from "./ui";

type Props = { adminKey: string; onAuthError: () => void };

const ROUTE_LABELS: Record<string, string> = {
  informational: "Informational",
  transactional: "Transactional",
  out_of_scope: "Out of scope",
  smalltalk: "Smalltalk",
};

// Display threshold for flagging a slow response. A UI choice, not a measured SLO.
const SLOW_MS = 3000;

const fmtMs = (ms: number) => (ms >= 1000 ? `${(ms / 1000).toFixed(2)} s` : `${Math.round(ms)} ms`);

function StatTile({ label, value, sub, flag }: { label: string; value: string; sub?: string; flag?: "slow" }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <p className="text-xs font-medium text-ink-3">{label}</p>
      <p className="mt-1.5 font-admin-mono text-3xl font-semibold tabular-nums tracking-tight text-ink">{value}</p>
      <div className="mt-1 flex min-h-5 items-center gap-2 text-xs text-ink-3">
        {flag === "slow" && (
          <span className="inline-flex items-center gap-1 rounded bg-warn-soft px-1.5 py-0.5 font-semibold text-warn">
            <Timer size={12} aria-hidden="true" /> Above {SLOW_MS / 1000} s
          </span>
        )}
        {sub && <span>{sub}</span>}
      </div>
    </div>
  );
}

function GroundedCell({ value }: { value: boolean | null }) {
  if (value === null)
    return (
      <span className="inline-flex items-center gap-1 text-ink-3">
        <CircleMinus size={14} aria-hidden="true" /> n/a
      </span>
    );
  return value ? (
    <span className="inline-flex items-center gap-1 text-ok">
      <CircleCheck size={14} aria-hidden="true" /> Yes
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-warn">
      <CircleX size={14} aria-hidden="true" /> No
    </span>
  );
}

export function MonitoringTab({ adminKey, onAuthError }: Props) {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [logs, setLogs] = useState<LogRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const [m, l] = await Promise.all([adminApi.metrics(adminKey), adminApi.logs(adminKey, 25)]);
      setMetrics(m);
      setLogs(l);
      setUpdatedAt(new Date());
    } catch (e) {
      if (e instanceof AdminAuthError) onAuthError();
      else setError(e instanceof Error ? e.message : "Failed to load metrics.");
    } finally {
      setLoading(false);
    }
  }, [adminKey, onAuthError]);

  useEffect(() => {
    void load();
  }, [load]);

  const routes = metrics ? Object.entries(metrics.by_route).sort((a, b) => b[1] - a[1]) : [];
  const routeTotal = routes.reduce((a, [, n]) => a + n, 0);
  const routeMax = routes.length ? routes[0][1] : 0;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-end gap-3">
        <UpdatedAt at={updatedAt} />
        <RefreshButton onClick={() => void load()} loading={loading} />
      </div>

      {error && <Notice tone="error">{error}</Notice>}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {metrics ? (
          <>
            <StatTile label="Total queries" value={metrics.total_queries.toLocaleString()} />
            <StatTile
              label="Grounded rate"
              value={metrics.grounded_rate === null ? "—" : `${Math.round(metrics.grounded_rate * 100)}%`}
              sub={`${metrics.grounded_queries} of ${metrics.informational_queries} informational`}
            />
            <StatTile label="Avg latency" value={fmtMs(metrics.avg_latency_ms)} flag={metrics.avg_latency_ms > SLOW_MS ? "slow" : undefined} />
            <StatTile label="P95 latency" value={fmtMs(metrics.p95_latency_ms)} flag={metrics.p95_latency_ms > SLOW_MS ? "slow" : undefined} />
          </>
        ) : (
          [0, 1, 2, 3].map((i) => (
            <div key={i} className="rounded-xl border border-line bg-surface p-4">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="mt-3 h-8 w-24" />
            </div>
          ))
        )}
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
        <Panel title="Route distribution" actions={<Gauge size={14} className="text-ink-3" aria-hidden="true" />}>
          <div className="p-4">
            {routeTotal === 0 ? (
              <p className="py-6 text-center text-sm text-ink-3">{loading ? "Loading…" : "No requests logged yet."}</p>
            ) : (
              // Single series: one hue, sorted, with the value printed beside each bar.
              <ul className="space-y-3.5">
                {routes.map(([route, n]) => {
                  const pct = Math.round((n / routeTotal) * 100);
                  return (
                    <li key={route} title={`${ROUTE_LABELS[route] ?? route}: ${n} requests (${pct}%)`}>
                      <div className="mb-1 flex items-baseline justify-between text-sm">
                        <span className="text-ink-2">{ROUTE_LABELS[route] ?? route}</span>
                        <span className="font-admin-mono tabular-nums text-ink">
                          {n} <span className="text-ink-3">· {pct}%</span>
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-surface-2">
                        <div
                          className="h-full rounded-full bg-brand transition-[width] duration-500"
                          style={{ width: `${routeMax ? (n / routeMax) * 100 : 0}%` }}
                        />
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </Panel>

        <Panel title={`Recent requests (${logs.length})`}>
          <div className="max-h-[480px] overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className={`sticky top-0 ${tableHead}`}>
                <tr>
                  <th className={th}>Time</th>
                  <th className={th}>Route</th>
                  <th className={th}>Message</th>
                  <th className={th}>Grounded</th>
                  <th className={`${th} text-right`}>Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {logs.map((r, i) => (
                  <tr key={i} className="transition-colors hover:bg-surface-2/60">
                    <td className={`${td} whitespace-nowrap font-admin-mono text-xs text-ink-3`}>
                      {new Date(r.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </td>
                    <td className={td}>
                      <span className="whitespace-nowrap rounded-md border border-line px-1.5 py-0.5 text-xs font-medium text-ink-2">
                        {ROUTE_LABELS[r.route] ?? r.route}
                      </span>
                    </td>
                    <td className={`${td} max-w-[22rem] truncate text-ink`} title={r.message}>
                      {r.message}
                      {r.outcome && <span className="ml-2 text-xs text-ink-3">{r.outcome}</span>}
                    </td>
                    <td className={`${td} whitespace-nowrap text-xs`}>
                      <GroundedCell value={r.grounded} />
                    </td>
                    <td
                      className={`${td} whitespace-nowrap text-right font-admin-mono text-xs tabular-nums ${
                        r.latency_ms > SLOW_MS ? "font-semibold text-warn" : "text-ink-2"
                      }`}
                    >
                      {r.latency_ms > SLOW_MS && <Timer size={12} className="mr-1 inline" aria-label="Slow" />}
                      {fmtMs(r.latency_ms)}
                    </td>
                  </tr>
                ))}
                {logs.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-10 text-center text-ink-3">
                      {loading ? "Loading…" : "No requests logged yet."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </div>
  );
}
