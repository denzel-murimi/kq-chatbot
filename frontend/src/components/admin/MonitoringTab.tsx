"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { adminApi, AdminAuthError, type LogRow, type Metrics } from "@/lib/admin-api";

type Props = { adminKey: string; onAuthError: () => void };

const ROUTE_LABELS: Record<string, string> = {
  informational: "Informational",
  transactional: "Transactional",
  out_of_scope: "Out of scope",
  smalltalk: "Smalltalk",
};

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

export function MonitoringTab({ adminKey, onAuthError }: Props) {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [logs, setLogs] = useState<LogRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [m, l] = await Promise.all([adminApi.metrics(adminKey), adminApi.logs(adminKey, 25)]);
      setMetrics(m);
      setLogs(l);
    } catch (e) {
      if (e instanceof AdminAuthError) onAuthError();
      else setError(e instanceof Error ? e.message : "Failed to load metrics.");
    }
  }, [adminKey, onAuthError]);

  useEffect(() => { void load(); }, [load]);

  const routeTotal = metrics ? Object.values(metrics.by_route).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-gray-700">Request metrics</h3>
        <button
          onClick={() => void load()}
          className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs font-semibold text-gray-600 transition hover:bg-gray-50"
        >
          <RefreshCw size={14} aria-hidden="true" /> Refresh
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {metrics && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Total queries" value={String(metrics.total_queries)} />
            <StatCard
              label="Grounded rate"
              value={metrics.grounded_rate === null ? "—" : `${Math.round(metrics.grounded_rate * 100)}%`}
            />
            <StatCard label="Avg latency" value={`${metrics.avg_latency_ms} ms`} />
            <StatCard label="P95 latency" value={`${metrics.p95_latency_ms} ms`} />
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-gray-500">Route distribution</p>
            <div className="space-y-2">
              {Object.entries(metrics.by_route).map(([route, n]) => (
                <div key={route} className="flex items-center gap-3">
                  <span className="w-28 shrink-0 text-sm text-gray-700">{ROUTE_LABELS[route] ?? route}</span>
                  <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-gray-100">
                    <div
                      className="h-full rounded-full bg-brand"
                      style={{ width: routeTotal ? `${(n / routeTotal) * 100}%` : "0%" }}
                    />
                  </div>
                  <span className="w-10 shrink-0 text-right text-sm font-semibold text-gray-700">{n}</span>
                </div>
              ))}
              {routeTotal === 0 && <p className="text-sm text-gray-500">No requests logged yet.</p>}
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
            <p className="border-b border-gray-100 px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
              Recent requests
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 text-[11px] uppercase tracking-wider text-gray-500">
                  <tr>
                    <th className="px-4 py-2 font-semibold">Time</th>
                    <th className="px-4 py-2 font-semibold">Route</th>
                    <th className="px-4 py-2 font-semibold">Message</th>
                    <th className="px-4 py-2 font-semibold">Outcome</th>
                    <th className="px-4 py-2 text-right font-semibold">ms</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((r, i) => (
                    <tr key={i} className="border-t border-gray-100">
                      <td className="whitespace-nowrap px-4 py-2 text-gray-500">
                        {new Date(r.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </td>
                      <td className="px-4 py-2 text-gray-700">{ROUTE_LABELS[r.route] ?? r.route}</td>
                      <td className="max-w-[22rem] truncate px-4 py-2 text-gray-800">{r.message}</td>
                      <td className="px-4 py-2 text-gray-600">{r.outcome ?? "—"}</td>
                      <td className="px-4 py-2 text-right text-gray-600">{r.latency_ms}</td>
                    </tr>
                  ))}
                  {logs.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-6 text-center text-gray-500">No requests logged yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}