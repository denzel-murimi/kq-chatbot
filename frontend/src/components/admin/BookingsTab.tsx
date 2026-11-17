"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { adminApi, AdminAuthError, type Booking } from "@/lib/admin-api";
import { Notice, Panel, RefreshButton, UpdatedAt, tableHead, td, th } from "./ui";

type Props = { adminKey: string; onAuthError: () => void };

// Neutral pill for any status; checked-in gets the positive tone. Text always carries the meaning.
function StatusPill({ status }: { status: string }) {
  const s = status.toLowerCase();
  const tone = s.includes("checked") ? "bg-ok-soft text-ok" : s.includes("cancel") ? "bg-danger-soft text-danger" : "bg-surface-2 text-ink-2";
  return <span className={`whitespace-nowrap rounded-md px-2 py-0.5 text-xs font-medium ${tone}`}>{status}</span>;
}

export function BookingsTab({ adminKey, onAuthError }: Props) {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const [query, setQuery] = useState("");

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      setBookings(await adminApi.bookings(adminKey));
      setUpdatedAt(new Date());
    } catch (e) {
      if (e instanceof AdminAuthError) onAuthError();
      else setError(e instanceof Error ? e.message : "Failed to load bookings.");
    } finally {
      setLoading(false);
    }
  }, [adminKey, onAuthError]);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return bookings;
    return bookings.filter((b) =>
      [b.pnr, b.first_name, b.last_name, b.flight_number, b.origin, b.destination].some((v) => v.toLowerCase().includes(q)),
    );
  }, [bookings, query]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-3" aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search PNR, name, flight…"
            aria-label="Search bookings"
            className="h-9 w-full rounded-lg border border-line-strong bg-surface pl-9 pr-3 text-sm text-ink outline-none placeholder:text-ink-3 focus:border-brand focus:ring-4 focus:ring-brand/15 focus-visible:outline-none"
          />
        </div>
        <div className="flex items-center gap-3">
          <UpdatedAt at={updatedAt} />
          <RefreshButton onClick={() => void load()} loading={loading} />
        </div>
      </div>

      {error && <Notice tone="error">{error}</Notice>}

      <Panel title={query ? `${filtered.length} of ${bookings.length} bookings` : `${bookings.length} bookings`}>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className={tableHead}>
              <tr>
                <th className={th}>PNR</th>
                <th className={th}>Passenger</th>
                <th className={th}>Flight</th>
                <th className={th}>Route</th>
                <th className={th}>Departure</th>
                <th className={th}>Seat</th>
                <th className={th}>Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {filtered.map((b) => (
                <tr key={b.pnr} className="transition-colors hover:bg-surface-2/60">
                  <td className={`${td} whitespace-nowrap font-admin-mono font-semibold text-ink`}>{b.pnr}</td>
                  <td className={`${td} whitespace-nowrap text-ink`}>
                    {b.first_name} {b.last_name}
                  </td>
                  <td className={`${td} whitespace-nowrap font-admin-mono text-ink-2`}>{b.flight_number}</td>
                  <td className={`${td} whitespace-nowrap font-admin-mono text-ink-2`}>
                    {b.origin} <span className="text-ink-3">→</span> {b.destination}
                  </td>
                  <td className={`${td} whitespace-nowrap tabular-nums text-ink-2`}>
                    {new Date(b.departure_time).toLocaleString([], {
                      day: "2-digit",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                  <td className={`${td} font-admin-mono font-semibold text-ink`}>{b.seat}</td>
                  <td className={td}>
                    <StatusPill status={b.status} />
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-ink-3">
                    {loading ? "Loading…" : query ? `No bookings match “${query}”.` : "No bookings found."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
